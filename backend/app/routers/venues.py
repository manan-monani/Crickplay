"""
Venues Router
Venue analytics (pitch type, avg scores, chase success rate)
"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import text

from app.dependencies import DbSession, TenantUser

router = APIRouter()


@router.get("/")
async def list_venues(
    user: TenantUser,
    db: DbSession,
    pitch_type: str = Query(None, description="Filter by pitch type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List venues with aggregated statistics."""
    offset = (page - 1) * page_size

    query = """
        SELECT venue_sk, stadium_name, matches_played,
               avg_first_innings_score, boundary_percentage,
               dot_ball_percentage, wicket_percentage,
               toss_impact_pct, chase_success_rate, pitch_type
        FROM gold.dim_venue
        WHERE 1=1
    """
    params = {}

    if pitch_type:
        query += " AND pitch_type = :pitch_type"
        params["pitch_type"] = pitch_type

    query += " ORDER BY matches_played DESC LIMIT :limit OFFSET :offset"
    params["limit"] = page_size
    params["offset"] = offset

    result = await db.execute(text(query), params)
    rows = result.mappings().all()
    return [dict(row) for row in rows]


@router.get("/{stadium_name}")
async def get_venue(stadium_name: str, user: TenantUser, db: DbSession):
    """Get detailed analytics for a specific venue."""
    query = """
        SELECT venue_sk, stadium_name, matches_played,
               avg_first_innings_score, min_first_innings_score,
               max_first_innings_score, boundary_percentage,
               dot_ball_percentage, wicket_percentage,
               toss_impact_pct, chase_success_rate, pitch_type
        FROM gold.dim_venue
        WHERE stadium_name = :stadium_name
    """
    result = await db.execute(text(query), {"stadium_name": stadium_name})
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
    return dict(row)

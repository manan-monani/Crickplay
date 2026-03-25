"""
Matches Router
Match analytics, win probability, and delivery-level data
"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import text

from app.dependencies import DbSession, TenantUser
from app.schemas.match import (
    DeliveryResponse,
    MatchSummaryResponse,
    WinProbabilityResponse,
)

router = APIRouter()


@router.get("/", response_model=list[MatchSummaryResponse])
async def list_matches(
    user: TenantUser,
    db: DbSession,
    team: str = Query(None, description="Filter by team name"),
    venue: str = Query(None, description="Filter by venue"),
    season: str = Query(None, description="Filter by season"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List matches with optional filters. Supports pagination."""
    offset = (page - 1) * page_size

    query = """
        SELECT
            match_id, match_date, venue,
            team_batting_first as team_1,
            team_batting_second as team_2,
            match_winner, win_margin,
            tournament_phase,
            first_innings_total,
            second_innings_total
        FROM gold.fact_match_summary
        WHERE 1=1
    """
    params = {}

    if team:
        query += " AND (team_batting_first = :team OR team_batting_second = :team)"
        params["team"] = team
    if venue:
        query += " AND venue ILIKE :venue"
        params["venue"] = f"%{venue}%"
    if season:
        query += " AND season = :season"
        params["season"] = season

    query += " ORDER BY match_date DESC LIMIT :limit OFFSET :offset"
    params["limit"] = page_size
    params["offset"] = offset

    result = await db.execute(text(query), params)
    rows = result.mappings().all()
    return [MatchSummaryResponse(**dict(row)) for row in rows]


@router.get("/{match_id}", response_model=MatchSummaryResponse)
async def get_match(match_id: str, user: TenantUser, db: DbSession):
    """Get a single match summary by match ID."""
    query = """
        SELECT
            match_id, match_date, venue,
            team_batting_first as team_1,
            team_batting_second as team_2,
            match_winner, win_margin,
            tournament_phase,
            first_innings_total,
            second_innings_total
        FROM gold.fact_match_summary
        WHERE match_id = :match_id
    """
    result = await db.execute(text(query), {"match_id": match_id})
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return MatchSummaryResponse(**dict(row))


@router.get("/{match_id}/deliveries", response_model=list[DeliveryResponse])
async def get_match_deliveries(
    match_id: str,
    user: TenantUser,
    db: DbSession,
    innings: int = Query(None, ge=1, le=2, description="Filter by innings"),
):
    """Get ball-by-ball deliveries for a match."""
    query = """
        SELECT
            delivery_id, innings_number, over_number, ball_number,
            batter, bowler, batter_runs, extra_runs, total_runs,
            is_wicket, is_boundary, wicket_kind
        FROM gold.fact_delivery
        WHERE match_id = :match_id
    """
    params = {"match_id": match_id}

    if innings:
        query += " AND innings_number = :innings"
        params["innings"] = innings

    query += " ORDER BY innings_number, over_number, ball_number"

    result = await db.execute(text(query), params)
    rows = result.mappings().all()
    return [DeliveryResponse(**dict(row)) for row in rows]


@router.get("/{match_id}/win-probability", response_model=WinProbabilityResponse)
async def get_win_probability(match_id: str, user: TenantUser, db: DbSession):
    """
    Get current win probability for a match.
    Returns the latest ML prediction with SHAP feature explanations.
    """
    # TODO: Integrate with ML model (Phase 5)
    # For now, return a placeholder based on match data
    query = """
        SELECT match_id, team_batting_first, team_batting_second,
               first_innings_total, second_innings_total, match_winner
        FROM gold.fact_match_summary
        WHERE match_id = :match_id
    """
    result = await db.execute(text(query), {"match_id": match_id})
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    row = dict(row)
    # Placeholder probability (will be replaced by ML model)
    team_1_prob = 0.5
    team_2_prob = 0.5

    if row["match_winner"]:
        if row["match_winner"] == row["team_batting_first"]:
            team_1_prob, team_2_prob = 1.0, 0.0
        else:
            team_1_prob, team_2_prob = 0.0, 1.0

    from datetime import datetime, timezone

    return WinProbabilityResponse(
        match_id=match_id,
        team_1=row["team_batting_first"],
        team_2=row["team_batting_second"],
        team_1_win_prob=team_1_prob,
        team_2_win_prob=team_2_prob,
        last_updated=datetime.now(timezone.utc),
        top_features=[],  # Populated by SHAP in Phase 5
    )

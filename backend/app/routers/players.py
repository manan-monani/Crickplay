"""
Players Router
Player analytics, stats, and matchup data
"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import text

from app.dependencies import DbSession, TenantUser
from app.schemas.player import PlayerResponse, PlayerStatsResponse

router = APIRouter()


@router.get("/", response_model=list[PlayerResponse])
async def list_players(
    user: TenantUser,
    db: DbSession,
    team: str = Query(None, description="Filter by national team"),
    role: str = Query(None, description="Filter by player role"),
    search: str = Query(None, description="Search player name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List players with optional filters."""
    offset = (page - 1) * page_size

    query = """
        SELECT player_name, national_team, player_role,
               total_balls_faced, total_runs_scored, career_strike_rate,
               total_balls_bowled, total_wickets_taken, career_economy_rate
        FROM gold.dim_player
        WHERE 1=1
    """
    params = {}

    if team:
        query += " AND national_team = :team"
        params["team"] = team
    if role:
        query += " AND player_role = :role"
        params["role"] = role
    if search:
        query += " AND player_name ILIKE :search"
        params["search"] = f"%{search}%"

    query += " ORDER BY total_runs_scored DESC LIMIT :limit OFFSET :offset"
    params["limit"] = page_size
    params["offset"] = offset

    result = await db.execute(text(query), params)
    rows = result.mappings().all()
    return [PlayerResponse(**dict(row)) for row in rows]


@router.get("/{player_name}", response_model=PlayerResponse)
async def get_player(player_name: str, user: TenantUser, db: DbSession):
    """Get a player profile by name."""
    query = """
        SELECT player_name, national_team, player_role,
               total_balls_faced, total_runs_scored, career_strike_rate,
               total_balls_bowled, total_wickets_taken, career_economy_rate
        FROM gold.dim_player
        WHERE player_name = :player_name
    """
    result = await db.execute(text(query), {"player_name": player_name})
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return PlayerResponse(**dict(row))


@router.get("/{player_name}/stats", response_model=PlayerStatsResponse)
async def get_player_stats(player_name: str, user: TenantUser, db: DbSession):
    """
    Get detailed player statistics with phase-wise breakdown.
    Computes powerplay/middle/death over splits.
    """
    # Base player info
    player_query = """
        SELECT player_name, national_team, player_role
        FROM gold.dim_player
        WHERE player_name = :player_name
    """
    result = await db.execute(text(player_query), {"player_name": player_name})
    player = result.mappings().first()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    # Phase-wise batting stats
    phase_query = """
        SELECT
            CASE
                WHEN over_number BETWEEN 0 AND 5 THEN 'powerplay'
                WHEN over_number BETWEEN 6 AND 14 THEN 'middle'
                ELSE 'death'
            END as phase,
            COUNT(*) as balls,
            SUM(batter_runs) as runs,
            CASE WHEN COUNT(*) > 0
                 THEN ROUND(SUM(batter_runs)::numeric / COUNT(*) * 100, 2)
                 ELSE 0
            END as strike_rate
        FROM gold.fact_delivery
        WHERE batter = :player_name
        GROUP BY phase
    """
    phase_result = await db.execute(text(phase_query), {"player_name": player_name})
    phases = {row["phase"]: row["strike_rate"] for row in phase_result.mappings().all()}

    return PlayerStatsResponse(
        player_name=player["player_name"],
        national_team=player["national_team"],
        player_role=player["player_role"],
        powerplay_strike_rate=phases.get("powerplay"),
        middle_overs_strike_rate=phases.get("middle"),
        death_overs_strike_rate=phases.get("death"),
    )

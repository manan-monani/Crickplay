"""
Players Router
Analytics endpoints for player statistics
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import random

from app.dependencies import get_current_user, get_db_with_tenant
from app.models.user import User
from app.schemas.player import (
    PlayerStatsResponse,
    BattingStats,
    BowlingStats,
)
from app.services.cache_service import cache_service

router = APIRouter()


@router.get("/{player_id}/stats", response_model=PlayerStatsResponse)
async def get_player_stats(
    player_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get comprehensive statistics for a player

    Includes batting, bowling, fielding stats and recent form
    Implements tenant isolation via RLS
    """
    # Check cache
    cache_key = cache_service.generate_key(
        "player_stats", str(current_user.tenant_id), player_id
    )
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return PlayerStatsResponse(**cached_data)

    # Mock data (replace with actual database query)
    players = {
        "virat_kohli": {
            "player_id": "virat_kohli",
            "name": "Virat Kohli",
            "team": "Royal Challengers Bangalore",
            "role": "Batsman",
        },
        "jasprit_bumrah": {
            "player_id": "jasprit_bumrah",
            "name": "Jasprit Bumrah",
            "team": "Mumbai Indians",
            "role": "Bowler",
        },
    }

    player_data = players.get(player_id)
    if not player_data:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player {player_id} not found",
        )

    # Generate mock statistics
    stats = {
        **player_data,
        "tenant_id": current_user.tenant_id,
        "batting": (
            {
                "matches": random.randint(150, 300),
                "innings": random.randint(140, 290),
                "runs": random.randint(5000, 10000),
                "highest_score": random.randint(80, 120),
                "average": round(random.uniform(30, 45), 2),
                "strike_rate": round(random.uniform(120, 150), 2),
                "centuries": random.randint(3, 10),
                "fifties": random.randint(30, 60),
                "fours": random.randint(500, 1000),
                "sixes": random.randint(150, 350),
            }
            if player_data["role"] in ["Batsman", "All-rounder"]
            else None
        ),
        "bowling": (
            {
                "matches": random.randint(150, 300),
                "innings": random.randint(140, 290),
                "overs": round(random.uniform(400, 800), 1),
                "wickets": random.randint(150, 300),
                "best_figures": "5/24",
                "average": round(random.uniform(18, 28), 2),
                "economy": round(random.uniform(6.5, 8.5), 2),
                "strike_rate": round(random.uniform(16, 22), 2),
                "five_wickets": random.randint(3, 10),
            }
            if player_data["role"] in ["Bowler", "All-rounder"]
            else None
        ),
        "fielding_catches": random.randint(50, 120),
        "fielding_stumpings": (
            random.randint(0, 20) if player_data["role"] == "WK" else 0
        ),
        "recent_form": {
            "last_5": {
                "runs": random.randint(150, 300),
                "average": round(random.uniform(30, 60), 1),
                "strike_rate": round(random.uniform(130, 160), 1),
            },
            "last_10": {
                "runs": random.randint(300, 550),
                "average": round(random.uniform(30, 55), 1),
                "strike_rate": round(random.uniform(125, 155), 1),
            },
        },
    }

    # Cache for 10 minutes
    await cache_service.set(cache_key, stats, ttl=600)

    return PlayerStatsResponse(**stats)

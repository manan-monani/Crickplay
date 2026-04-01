"""
Matches Router
Analytics endpoints for match data and predictions
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import random

from app.dependencies import get_current_user, get_db_with_tenant, require_role
from app.models.user import User
from app.schemas.match import (
    MatchResponse,
    MatchListResponse,
    WinProbability,
    MatchFilters,
)
from app.services.cache_service import cache_service

router = APIRouter()


# Mock data generator (replace with actual database queries later)
def generate_mock_matches(tenant_id: UUID, count: int = 10) -> list:
    """Generate mock match data for demonstration"""
    teams = [
        "Mumbai Indians",
        "Chennai Super Kings",
        "Royal Challengers Bangalore",
        "Kolkata Knight Riders",
        "Delhi Capitals",
        "Rajasthan Royals",
        "Punjab Kings",
        "Sunrisers Hyderabad",
        "Gujarat Titans",
        "Lucknow Super Giants",
    ]
    venues = [
        "Wankhede Stadium",
        "MA Chidambaram Stadium",
        "M. Chinnaswamy Stadium",
        "Eden Gardens",
        "Arun Jaitley Stadium",
        "Sawai Mansingh Stadium",
    ]

    matches = []
    base_date = datetime.now() - timedelta(days=60)

    for i in range(count):
        team1, team2 = random.sample(teams, 2)
        venue = random.choice(venues)
        match_date = base_date + timedelta(days=i * 3)

        matches.append(
            {
                "match_id": f"IPL2024_{i+1:03d}",
                "tenant_id": tenant_id,
                "team1": team1,
                "team2": team2,
                "venue": venue,
                "match_date": match_date,
                "match_type": "T20",
                "winner": team1 if random.random() > 0.5 else team2,
                "result": f"{team1 if random.random() > 0.5 else team2} won by {random.randint(1, 50)} runs",
                "total_runs": random.randint(250, 400),
                "total_wickets": random.randint(10, 20),
            }
        )

    return matches


@router.get("", response_model=MatchListResponse)
async def get_matches(
    team: Optional[str] = Query(None, description="Filter by team name"),
    venue: Optional[str] = Query(None, description="Filter by venue"),
    match_type: Optional[str] = Query(None, description="Filter by match type"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get paginated list of matches

    Supports filtering by team, venue, match type, and date range
    Implements tenant isolation via RLS
    """
    # Check cache first
    cache_key = cache_service.generate_key(
        "matches",
        str(current_user.tenant_id),
        str(team or "all"),
        str(venue or "all"),
        str(page),
    )

    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data

    # Mock data for demonstration (replace with actual database query)
    all_matches = generate_mock_matches(current_user.tenant_id, count=50)

    # Apply filters
    filtered_matches = all_matches
    if team:
        filtered_matches = [
            m
            for m in filtered_matches
            if team.lower() in m["team1"].lower() or team.lower() in m["team2"].lower()
        ]
    if venue:
        filtered_matches = [
            m for m in filtered_matches if venue.lower() in m["venue"].lower()
        ]
    if match_type:
        filtered_matches = [
            m for m in filtered_matches if m["match_type"] == match_type
        ]
    if date_from:
        filtered_matches = [m for m in filtered_matches if m["match_date"] >= date_from]
    if date_to:
        filtered_matches = [m for m in filtered_matches if m["match_date"] <= date_to]

    # Pagination
    total = len(filtered_matches)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_matches = filtered_matches[start:end]

    response = {
        "matches": [MatchResponse(**m) for m in paginated_matches],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

    # Cache for 5 minutes
    await cache_service.set(cache_key, response, ttl=300)

    return response


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get details of a specific match

    Implements tenant isolation via RLS
    """
    # Check cache
    cache_key = cache_service.generate_key(
        "match", str(current_user.tenant_id), match_id
    )
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return MatchResponse(**cached_data)

    # Mock data (replace with actual database query)
    matches = generate_mock_matches(current_user.tenant_id, count=50)
    match = next((m for m in matches if m["match_id"] == match_id), None)

    if not match:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Match {match_id} not found"
        )

    # Cache for 5 minutes
    await cache_service.set(cache_key, match, ttl=300)

    return MatchResponse(**match)


@router.get("/{match_id}/win-probability", response_model=WinProbability)
async def get_win_probability(
    match_id: str,
    current_user: User = Depends(require_role(["professional", "enterprise", "admin"])),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get live win probability prediction for a match

    **Requires Professional or Enterprise subscription**

    Uses ML models trained on historical data to predict match outcome
    Cached for performance
    """
    # Check cache
    cache_key = cache_service.generate_key(
        "win_probability", str(current_user.tenant_id), match_id
    )
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return WinProbability(**cached_data)

    # Mock data (replace with actual ML model prediction)
    team1_prob = random.uniform(0.3, 0.7)
    team2_prob = 1 - team1_prob

    prediction = {
        "match_id": match_id,
        "team1": "Mumbai Indians",
        "team2": "Chennai Super Kings",
        "team1_probability": round(team1_prob, 2),
        "team2_probability": round(team2_prob, 2),
        "current_over": random.randint(10, 19),
        "current_score": f"{random.randint(120, 180)}/{random.randint(2, 6)}",
        "predicted_winner": (
            "Mumbai Indians" if team1_prob > team2_prob else "Chennai Super Kings"
        ),
        "confidence": round(
            abs(team1_prob - 0.5) * 2, 2
        ),  # 0.5 = 50/50, 1.0 = 100% confident
    }

    # Cache for 1 minute (live data updates frequently)
    await cache_service.set(cache_key, prediction, ttl=60)

    return WinProbability(**prediction)

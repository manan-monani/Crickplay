"""
Venues Router
Analytics endpoints for venue statistics and pitch reports
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import random

from app.dependencies import get_current_user, get_db_with_tenant
from app.models.user import User
from app.schemas.venue import VenueAnalyticsResponse, VenueStats
from app.services.cache_service import cache_service

router = APIRouter()


@router.get("/{venue_id}/analytics", response_model=VenueAnalyticsResponse)
async def get_venue_analytics(
    venue_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get comprehensive analytics for a venue

    Includes pitch characteristics, historical data, weather impact
    Implements tenant isolation via RLS
    """
    # Check cache
    cache_key = cache_service.generate_key(
        "venue_analytics", str(current_user.tenant_id), venue_id
    )
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return VenueAnalyticsResponse(**cached_data)

    # Mock data (replace with actual database query)
    venues = {
        "wankhede": {
            "venue_id": "wankhede",
            "name": "Wankhede Stadium",
            "city": "Mumbai",
            "country": "India",
            "capacity": 33000,
        },
        "eden_gardens": {
            "venue_id": "eden_gardens",
            "name": "Eden Gardens",
            "city": "Kolkata",
            "country": "India",
            "capacity": 66000,
        },
    }

    venue_data = venues.get(venue_id)
    if not venue_data:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Venue {venue_id} not found"
        )

    # Generate mock analytics
    analytics = {
        **venue_data,
        "tenant_id": current_user.tenant_id,
        "stats": {
            "matches_played": random.randint(100, 200),
            "average_first_innings": round(random.uniform(160, 180), 1),
            "average_second_innings": round(random.uniform(150, 170), 1),
            "highest_team_score": random.randint(220, 250),
            "lowest_team_score": random.randint(80, 110),
            "win_percentage_batting_first": round(random.uniform(45, 55), 1),
            "win_percentage_chasing": round(random.uniform(45, 55), 1),
        },
        "pitch_report": {
            "surface": random.choice(
                ["Balanced", "Batting-friendly", "Spin-friendly", "Pace-friendly"]
            ),
            "pace_bounce": random.choice(["Low", "Medium", "High"]),
            "spin_friendliness": random.choice(["Low", "Moderate", "High"]),
            "favors": random.choice(
                [
                    "Batsmen in first innings",
                    "Batsmen throughout",
                    "Bowlers in second innings",
                    "Balanced for both",
                ]
            ),
        },
        "weather_impact": {
            "dew_factor": random.choice(["Low", "Medium", "High"])
            + " in evening matches",
            "typical_temperature": f"{random.randint(25, 35)}-{random.randint(30, 40)}°C",
        },
    }

    # Cache for 1 hour (venue stats don't change frequently)
    await cache_service.set(cache_key, analytics, ttl=3600)

    return VenueAnalyticsResponse(**analytics)

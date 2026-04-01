"""
Venue Analytics Pydantic Schemas
Request/response models for venue endpoints
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any
from uuid import UUID


class VenueBase(BaseModel):
    """Base venue schema"""

    venue_id: str = Field(..., description="Venue identifier")
    name: str = Field(..., description="Venue name")
    city: str = Field(..., description="City")
    country: str = Field(..., description="Country")
    capacity: int = Field(..., ge=0, description="Seating capacity")


class VenueStats(BaseModel):
    """Venue statistics"""

    matches_played: int = Field(..., ge=0)
    average_first_innings: float = Field(..., ge=0)
    average_second_innings: float = Field(..., ge=0)
    highest_team_score: int = Field(..., ge=0)
    lowest_team_score: int = Field(..., ge=0)
    win_percentage_batting_first: float = Field(..., ge=0, le=100)
    win_percentage_chasing: float = Field(..., ge=0, le=100)


class VenueAnalyticsResponse(VenueBase):
    """Venue analytics response with historical data"""

    tenant_id: UUID
    stats: VenueStats
    pitch_report: Dict[str, Any] = Field(
        default_factory=dict, description="Pitch characteristics and trends"
    )
    weather_impact: Dict[str, Any] = Field(
        default_factory=dict, description="Weather impact on matches"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "venue_id": "wankhede",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Wankhede Stadium",
                "city": "Mumbai",
                "country": "India",
                "capacity": 33000,
                "stats": {
                    "matches_played": 150,
                    "average_first_innings": 165.5,
                    "average_second_innings": 158.3,
                    "highest_team_score": 235,
                    "lowest_team_score": 87,
                    "win_percentage_batting_first": 52.5,
                    "win_percentage_chasing": 47.5,
                },
                "pitch_report": {
                    "surface": "Balanced",
                    "pace_bounce": "Medium",
                    "spin_friendliness": "Moderate",
                    "favors": "Batsmen in first innings",
                },
                "weather_impact": {
                    "dew_factor": "High in evening matches",
                    "typical_temperature": "28-32°C",
                },
            }
        },
    )

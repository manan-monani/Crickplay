"""
Player Statistics Pydantic Schemas
Request/response models for player endpoints
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class PlayerBase(BaseModel):
    """Base player schema"""

    player_id: str = Field(..., description="Player identifier")
    name: str = Field(..., description="Player full name")
    team: str = Field(..., description="Current team")
    role: str = Field(..., description="Player role (Batsman, Bowler, All-rounder, WK)")


class BattingStats(BaseModel):
    """Batting statistics"""

    matches: int = Field(..., ge=0)
    innings: int = Field(..., ge=0)
    runs: int = Field(..., ge=0)
    highest_score: int = Field(..., ge=0)
    average: float = Field(..., ge=0)
    strike_rate: float = Field(..., ge=0)
    centuries: int = Field(..., ge=0)
    fifties: int = Field(..., ge=0)
    fours: int = Field(..., ge=0)
    sixes: int = Field(..., ge=0)


class BowlingStats(BaseModel):
    """Bowling statistics"""

    matches: int = Field(..., ge=0)
    innings: int = Field(..., ge=0)
    overs: float = Field(..., ge=0)
    wickets: int = Field(..., ge=0)
    best_figures: str = Field(..., description="Best bowling figures (e.g., '5/24')")
    average: float = Field(..., ge=0)
    economy: float = Field(..., ge=0)
    strike_rate: float = Field(..., ge=0)
    five_wickets: int = Field(..., ge=0)


class PlayerStatsResponse(PlayerBase):
    """Complete player statistics response"""

    tenant_id: UUID
    batting: Optional[BattingStats] = None
    bowling: Optional[BowlingStats] = None
    fielding_catches: int = Field(0, ge=0)
    fielding_stumpings: int = Field(0, ge=0)

    # Phase-wise stats (last 5, 10, 20 matches)
    recent_form: Dict[str, Any] = Field(
        default_factory=dict, description="Recent form statistics"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "player_id": "virat_kohli",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Virat Kohli",
                "team": "Royal Challengers Bangalore",
                "role": "Batsman",
                "batting": {
                    "matches": 250,
                    "innings": 245,
                    "runs": 7500,
                    "highest_score": 113,
                    "average": 37.5,
                    "strike_rate": 130.5,
                    "centuries": 7,
                    "fifties": 50,
                    "fours": 700,
                    "sixes": 250,
                },
                "fielding_catches": 95,
                "fielding_stumpings": 0,
                "recent_form": {
                    "last_5": {"runs": 245, "average": 49.0, "strike_rate": 145.2},
                    "last_10": {"runs": 452, "average": 45.2, "strike_rate": 138.5},
                },
            }
        },
    )

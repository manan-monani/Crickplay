"""
Match Analytics Pydantic Schemas
Request/response models for match endpoints
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Base schemas
class MatchBase(BaseModel):
    """Base match schema"""

    match_id: str = Field(..., description="Match identifier")
    team1: str = Field(..., description="First team name")
    team2: str = Field(..., description="Second team name")
    venue: str = Field(..., description="Venue name")
    match_date: datetime = Field(..., description="Match date and time")
    match_type: str = Field(..., description="Match type (T20, ODI, Test)")


class MatchResponse(MatchBase):
    """Match response schema"""

    tenant_id: UUID = Field(..., description="Tenant ID (multi-tenancy)")
    winner: Optional[str] = Field(None, description="Winning team")
    result: Optional[str] = Field(None, description="Match result description")
    total_runs: Optional[int] = Field(None, description="Total runs scored")
    total_wickets: Optional[int] = Field(None, description="Total wickets fallen")

    model_config = ConfigDict(from_attributes=True)


class MatchListResponse(BaseModel):
    """Paginated match list response"""

    matches: List[MatchResponse]
    total: int = Field(..., description="Total number of matches")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "matches": [
                    {
                        "match_id": "IPL2024_001",
                        "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                        "team1": "Mumbai Indians",
                        "team2": "Chennai Super Kings",
                        "venue": "Wankhede Stadium",
                        "match_date": "2024-03-22T19:30:00",
                        "match_type": "T20",
                        "winner": "Mumbai Indians",
                        "result": "MI won by 5 wickets",
                        "total_runs": 340,
                        "total_wickets": 15,
                    }
                ],
                "total": 100,
                "page": 1,
                "page_size": 10,
            }
        }
    )


class WinProbability(BaseModel):
    """Win probability response"""

    match_id: str
    team1: str
    team2: str
    team1_probability: float = Field(
        ..., ge=0, le=1, description="Team 1 win probability (0-1)"
    )
    team2_probability: float = Field(
        ..., ge=0, le=1, description="Team 2 win probability (0-1)"
    )
    current_over: int = Field(..., ge=0, description="Current over number")
    current_score: str = Field(..., description="Current score (e.g., '150/4')")
    predicted_winner: str = Field(..., description="Predicted winner")
    confidence: float = Field(
        ..., ge=0, le=1, description="Prediction confidence (0-1)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "match_id": "IPL2024_001",
                "team1": "Mumbai Indians",
                "team2": "Chennai Super Kings",
                "team1_probability": 0.65,
                "team2_probability": 0.35,
                "current_over": 15,
                "current_score": "145/3",
                "predicted_winner": "Mumbai Indians",
                "confidence": 0.82,
            }
        }
    )


class MatchFilters(BaseModel):
    """Query filters for match list"""

    team: Optional[str] = Field(None, description="Filter by team name")
    venue: Optional[str] = Field(None, description="Filter by venue")
    match_type: Optional[str] = Field(None, description="Filter by match type")
    date_from: Optional[datetime] = Field(
        None, description="Filter matches from this date"
    )
    date_to: Optional[datetime] = Field(None, description="Filter matches to this date")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Items per page")

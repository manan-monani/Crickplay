"""
Match Pydantic Schemas
Request/response models for match analytics endpoints
"""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class MatchSummaryResponse(BaseModel):
    """Match summary for list endpoint."""
    match_id: str
    match_date: date
    venue: str
    team_1: str
    team_2: str
    match_winner: Optional[str] = None
    win_margin: Optional[str] = None
    tournament_phase: Optional[str] = None
    first_innings_total: int
    second_innings_total: int

    model_config = {"from_attributes": True}


class WinProbabilityResponse(BaseModel):
    """Live win probability response."""
    match_id: str
    team_1: str
    team_2: str
    team_1_win_prob: float = Field(..., ge=0, le=1)
    team_2_win_prob: float = Field(..., ge=0, le=1)
    last_updated: datetime

    # SHAP explanation
    top_features: list[dict] = Field(
        default_factory=list,
        description="Top 3 SHAP feature contributions"
    )


class DeliveryResponse(BaseModel):
    """Single delivery event."""
    delivery_id: str
    innings_number: int
    over_number: int
    ball_number: int
    batter: str
    bowler: str
    batter_runs: int
    extra_runs: int
    total_runs: int
    is_wicket: bool
    is_boundary: bool
    wicket_kind: Optional[str] = None

    model_config = {"from_attributes": True}


class MatchFilters(BaseModel):
    """Query filters for match listing."""
    team: Optional[str] = None
    venue: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    tournament_phase: Optional[str] = None
    season: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

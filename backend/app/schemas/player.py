"""
Player Pydantic Schemas
Request/response models for player analytics endpoints
"""

from typing import Optional

from pydantic import BaseModel, Field


class PlayerResponse(BaseModel):
    """Player profile with career stats."""
    player_name: str
    national_team: str
    player_role: str

    # Batting
    total_balls_faced: int
    total_runs_scored: int
    career_strike_rate: float

    # Bowling
    total_balls_bowled: int
    total_wickets_taken: int
    career_economy_rate: float

    model_config = {"from_attributes": True}


class PlayerStatsResponse(BaseModel):
    """Detailed player statistics with phase-wise breakdown."""
    player_name: str
    national_team: str
    player_role: str

    # Rolling averages (last 10 innings)
    rolling_strike_rate: Optional[float] = None
    rolling_economy: Optional[float] = None

    # Phase-wise stats
    powerplay_strike_rate: Optional[float] = None
    middle_overs_strike_rate: Optional[float] = None
    death_overs_strike_rate: Optional[float] = None

    # Head-to-head matchup summary
    best_matchup_against: Optional[str] = None
    worst_matchup_against: Optional[str] = None

    model_config = {"from_attributes": True}


class FantasyProjectionResponse(BaseModel):
    """Fantasy points projection for a player."""
    player_name: str
    expected_runs: float = Field(ge=0)
    expected_wickets: float = Field(ge=0)
    catch_probability: float = Field(ge=0, le=1)
    projected_points: float
    confidence: float = Field(ge=0, le=1, description="Model confidence")

    model_config = {"from_attributes": True}

"""
Team Profiles for Synthetic Data Generation

Defines team strength profiles based on historical performance data.
These profiles are used by the Monte Carlo simulator to generate
realistic synthetic match outcomes for teams with limited historical data.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class BattingStyle(Enum):
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    DEFENSIVE = "defensive"


class BowlingStrength(Enum):
    PACE_DOMINANT = "pace_dominant"
    SPIN_DOMINANT = "spin_dominant"
    BALANCED = "balanced"


@dataclass
class TeamProfile:
    """Represents a team's statistical profile for simulation."""

    name: str
    icc_ranking: int  # T20I ranking (1-20+)

    # Batting metrics (average performance)
    avg_powerplay_runs: float  # Overs 1-6
    avg_middle_overs_runs: float  # Overs 7-15
    avg_death_overs_runs: float  # Overs 16-20
    batting_style: BattingStyle

    # Bowling metrics
    avg_powerplay_economy: float
    avg_middle_economy: float
    avg_death_economy: float
    bowling_strength: BowlingStrength
    avg_wickets_per_match: float

    # Match win probability base (adjusted by opponent)
    base_win_probability: float

    # Volatility (higher = more unpredictable)
    volatility: float

    def __post_init__(self):
        """Validate profile constraints."""
        if not 0 <= self.base_win_probability <= 1:
            raise ValueError("Win probability must be between 0 and 1")
        if not 0 <= self.volatility <= 1:
            raise ValueError("Volatility must be between 0 and 1")


# Established T20I teams based on historical data
ESTABLISHED_TEAMS: Dict[str, TeamProfile] = {
    "India": TeamProfile(
        name="India",
        icc_ranking=1,
        avg_powerplay_runs=52.0,
        avg_middle_overs_runs=58.0,
        avg_death_overs_runs=55.0,
        batting_style=BattingStyle.AGGRESSIVE,
        avg_powerplay_economy=7.2,
        avg_middle_economy=7.8,
        avg_death_economy=9.5,
        bowling_strength=BowlingStrength.BALANCED,
        avg_wickets_per_match=6.5,
        base_win_probability=0.65,
        volatility=0.15,
    ),
    "England": TeamProfile(
        name="England",
        icc_ranking=2,
        avg_powerplay_runs=54.0,
        avg_middle_overs_runs=56.0,
        avg_death_overs_runs=58.0,
        batting_style=BattingStyle.AGGRESSIVE,
        avg_powerplay_economy=7.5,
        avg_middle_economy=8.0,
        avg_death_economy=9.8,
        bowling_strength=BowlingStrength.PACE_DOMINANT,
        avg_wickets_per_match=6.2,
        base_win_probability=0.62,
        volatility=0.18,
    ),
    "Australia": TeamProfile(
        name="Australia",
        icc_ranking=3,
        avg_powerplay_runs=50.0,
        avg_middle_overs_runs=55.0,
        avg_death_overs_runs=56.0,
        batting_style=BattingStyle.BALANCED,
        avg_powerplay_economy=7.0,
        avg_middle_economy=7.5,
        avg_death_economy=9.2,
        bowling_strength=BowlingStrength.PACE_DOMINANT,
        avg_wickets_per_match=6.8,
        base_win_probability=0.60,
        volatility=0.15,
    ),
    "Pakistan": TeamProfile(
        name="Pakistan",
        icc_ranking=4,
        avg_powerplay_runs=48.0,
        avg_middle_overs_runs=52.0,
        avg_death_overs_runs=54.0,
        batting_style=BattingStyle.BALANCED,
        avg_powerplay_economy=7.8,
        avg_middle_economy=7.6,
        avg_death_economy=9.0,
        bowling_strength=BowlingStrength.PACE_DOMINANT,
        avg_wickets_per_match=7.0,
        base_win_probability=0.55,
        volatility=0.25,
    ),
    "South Africa": TeamProfile(
        name="South Africa",
        icc_ranking=5,
        avg_powerplay_runs=49.0,
        avg_middle_overs_runs=54.0,
        avg_death_overs_runs=52.0,
        batting_style=BattingStyle.BALANCED,
        avg_powerplay_economy=7.2,
        avg_middle_economy=7.4,
        avg_death_economy=9.3,
        bowling_strength=BowlingStrength.PACE_DOMINANT,
        avg_wickets_per_match=6.5,
        base_win_probability=0.55,
        volatility=0.20,
    ),
    "New Zealand": TeamProfile(
        name="New Zealand",
        icc_ranking=6,
        avg_powerplay_runs=46.0,
        avg_middle_overs_runs=50.0,
        avg_death_overs_runs=48.0,
        batting_style=BattingStyle.BALANCED,
        avg_powerplay_economy=7.0,
        avg_middle_economy=7.2,
        avg_death_economy=8.8,
        bowling_strength=BowlingStrength.BALANCED,
        avg_wickets_per_match=6.3,
        base_win_probability=0.52,
        volatility=0.15,
    ),
    "West Indies": TeamProfile(
        name="West Indies",
        icc_ranking=7,
        avg_powerplay_runs=52.0,
        avg_middle_overs_runs=48.0,
        avg_death_overs_runs=55.0,
        batting_style=BattingStyle.AGGRESSIVE,
        avg_powerplay_economy=8.0,
        avg_middle_economy=8.2,
        avg_death_economy=9.5,
        bowling_strength=BowlingStrength.PACE_DOMINANT,
        avg_wickets_per_match=5.8,
        base_win_probability=0.50,
        volatility=0.30,
    ),
    "Sri Lanka": TeamProfile(
        name="Sri Lanka",
        icc_ranking=8,
        avg_powerplay_runs=44.0,
        avg_middle_overs_runs=48.0,
        avg_death_overs_runs=45.0,
        batting_style=BattingStyle.BALANCED,
        avg_powerplay_economy=7.5,
        avg_middle_economy=7.0,
        avg_death_economy=8.5,
        bowling_strength=BowlingStrength.SPIN_DOMINANT,
        avg_wickets_per_match=6.0,
        base_win_probability=0.48,
        volatility=0.22,
    ),
    "Bangladesh": TeamProfile(
        name="Bangladesh",
        icc_ranking=9,
        avg_powerplay_runs=42.0,
        avg_middle_overs_runs=45.0,
        avg_death_overs_runs=42.0,
        batting_style=BattingStyle.DEFENSIVE,
        avg_powerplay_economy=7.8,
        avg_middle_economy=7.2,
        avg_death_economy=9.0,
        bowling_strength=BowlingStrength.SPIN_DOMINANT,
        avg_wickets_per_match=5.5,
        base_win_probability=0.42,
        volatility=0.25,
    ),
    "Afghanistan": TeamProfile(
        name="Afghanistan",
        icc_ranking=10,
        avg_powerplay_runs=45.0,
        avg_middle_overs_runs=42.0,
        avg_death_overs_runs=40.0,
        batting_style=BattingStyle.AGGRESSIVE,
        avg_powerplay_economy=7.0,
        avg_middle_economy=6.5,
        avg_death_economy=8.0,
        bowling_strength=BowlingStrength.SPIN_DOMINANT,
        avg_wickets_per_match=6.8,
        base_win_probability=0.45,
        volatility=0.28,
    ),
}

# Emerging/Associate teams for 2026 World Cup
EMERGING_TEAMS: Dict[str, TeamProfile] = {
    "Italy": TeamProfile(
        name="Italy",
        icc_ranking=35,
        avg_powerplay_runs=32.0,
        avg_middle_overs_runs=35.0,
        avg_death_overs_runs=30.0,
        batting_style=BattingStyle.DEFENSIVE,
        avg_powerplay_economy=9.5,
        avg_middle_economy=9.0,
        avg_death_economy=11.0,
        bowling_strength=BowlingStrength.BALANCED,
        avg_wickets_per_match=4.0,
        base_win_probability=0.20,
        volatility=0.35,
    ),
    "Canada": TeamProfile(
        name="Canada",
        icc_ranking=18,
        avg_powerplay_runs=38.0,
        avg_middle_overs_runs=40.0,
        avg_death_overs_runs=35.0,
        batting_style=BattingStyle.BALANCED,
        avg_powerplay_economy=8.5,
        avg_middle_economy=8.2,
        avg_death_economy=10.0,
        bowling_strength=BowlingStrength.PACE_DOMINANT,
        avg_wickets_per_match=4.5,
        base_win_probability=0.30,
        volatility=0.30,
    ),
    "Oman": TeamProfile(
        name="Oman",
        icc_ranking=16,
        avg_powerplay_runs=36.0,
        avg_middle_overs_runs=38.0,
        avg_death_overs_runs=34.0,
        batting_style=BattingStyle.DEFENSIVE,
        avg_powerplay_economy=8.0,
        avg_middle_economy=7.5,
        avg_death_economy=9.5,
        bowling_strength=BowlingStrength.BALANCED,
        avg_wickets_per_match=5.0,
        base_win_probability=0.32,
        volatility=0.28,
    ),
    "USA": TeamProfile(
        name="USA",
        icc_ranking=15,
        avg_powerplay_runs=40.0,
        avg_middle_overs_runs=42.0,
        avg_death_overs_runs=38.0,
        batting_style=BattingStyle.AGGRESSIVE,
        avg_powerplay_economy=8.2,
        avg_middle_economy=8.0,
        avg_death_economy=9.8,
        bowling_strength=BowlingStrength.PACE_DOMINANT,
        avg_wickets_per_match=4.8,
        base_win_probability=0.35,
        volatility=0.32,
    ),
    "Netherlands": TeamProfile(
        name="Netherlands",
        icc_ranking=14,
        avg_powerplay_runs=42.0,
        avg_middle_overs_runs=44.0,
        avg_death_overs_runs=40.0,
        batting_style=BattingStyle.BALANCED,
        avg_powerplay_economy=8.0,
        avg_middle_economy=7.8,
        avg_death_economy=9.5,
        bowling_strength=BowlingStrength.PACE_DOMINANT,
        avg_wickets_per_match=5.2,
        base_win_probability=0.38,
        volatility=0.25,
    ),
    "Ireland": TeamProfile(
        name="Ireland",
        icc_ranking=12,
        avg_powerplay_runs=44.0,
        avg_middle_overs_runs=46.0,
        avg_death_overs_runs=42.0,
        batting_style=BattingStyle.BALANCED,
        avg_powerplay_economy=7.8,
        avg_middle_economy=7.5,
        avg_death_economy=9.2,
        bowling_strength=BowlingStrength.PACE_DOMINANT,
        avg_wickets_per_match=5.5,
        base_win_probability=0.40,
        volatility=0.22,
    ),
    "Scotland": TeamProfile(
        name="Scotland",
        icc_ranking=13,
        avg_powerplay_runs=43.0,
        avg_middle_overs_runs=44.0,
        avg_death_overs_runs=40.0,
        batting_style=BattingStyle.DEFENSIVE,
        avg_powerplay_economy=7.9,
        avg_middle_economy=7.6,
        avg_death_economy=9.3,
        bowling_strength=BowlingStrength.BALANCED,
        avg_wickets_per_match=5.3,
        base_win_probability=0.38,
        volatility=0.24,
    ),
    "Nepal": TeamProfile(
        name="Nepal",
        icc_ranking=17,
        avg_powerplay_runs=38.0,
        avg_middle_overs_runs=40.0,
        avg_death_overs_runs=36.0,
        batting_style=BattingStyle.AGGRESSIVE,
        avg_powerplay_economy=8.0,
        avg_middle_economy=7.0,
        avg_death_economy=9.0,
        bowling_strength=BowlingStrength.SPIN_DOMINANT,
        avg_wickets_per_match=5.5,
        base_win_probability=0.35,
        volatility=0.30,
    ),
    "UAE": TeamProfile(
        name="UAE",
        icc_ranking=19,
        avg_powerplay_runs=35.0,
        avg_middle_overs_runs=38.0,
        avg_death_overs_runs=32.0,
        batting_style=BattingStyle.DEFENSIVE,
        avg_powerplay_economy=8.5,
        avg_middle_economy=8.0,
        avg_death_economy=10.0,
        bowling_strength=BowlingStrength.SPIN_DOMINANT,
        avg_wickets_per_match=4.5,
        base_win_probability=0.28,
        volatility=0.30,
    ),
    "Namibia": TeamProfile(
        name="Namibia",
        icc_ranking=20,
        avg_powerplay_runs=36.0,
        avg_middle_overs_runs=38.0,
        avg_death_overs_runs=34.0,
        batting_style=BattingStyle.DEFENSIVE,
        avg_powerplay_economy=8.2,
        avg_middle_economy=7.8,
        avg_death_economy=9.5,
        bowling_strength=BowlingStrength.PACE_DOMINANT,
        avg_wickets_per_match=5.0,
        base_win_probability=0.30,
        volatility=0.28,
    ),
}

# Combined profiles
ALL_TEAMS: Dict[str, TeamProfile] = {**ESTABLISHED_TEAMS, **EMERGING_TEAMS}


def get_team_profile(team_name: str) -> Optional[TeamProfile]:
    """Get a team profile by name."""
    return ALL_TEAMS.get(team_name)


def get_all_team_names() -> List[str]:
    """Get list of all team names."""
    return list(ALL_TEAMS.keys())


def calculate_head_to_head_probability(
    team_a: TeamProfile, team_b: TeamProfile
) -> float:
    """
    Calculate adjusted win probability for team_a against team_b.
    Uses Elo-style calculation based on base probabilities and rankings.
    """
    # Base probability difference
    prob_diff = team_a.base_win_probability - team_b.base_win_probability

    # Ranking adjustment (higher ranked team gets slight boost)
    ranking_factor = (team_b.icc_ranking - team_a.icc_ranking) / 50.0
    ranking_factor = max(-0.1, min(0.1, ranking_factor))  # Cap adjustment

    # Calculate final probability
    adjusted_prob = 0.5 + (prob_diff * 0.8) + ranking_factor

    # Ensure valid probability range
    return max(0.05, min(0.95, adjusted_prob))

"""
Monte Carlo Simulation Engine for Cricket Match Generation

Uses probabilistic simulations to generate realistic ball-by-ball
match data based on team strength profiles.
"""

import random
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .team_profiles import (
    TeamProfile,
    BattingStyle,
    BowlingStrength,
    calculate_head_to_head_probability,
)


class DismissalType(Enum):
    BOWLED = "bowled"
    CAUGHT = "caught"
    LBW = "lbw"
    RUN_OUT = "run out"
    STUMPED = "stumped"
    HIT_WICKET = "hit wicket"
    CAUGHT_AND_BOWLED = "caught and bowled"


@dataclass
class DeliveryOutcome:
    """Outcome of a single delivery."""

    runs_off_bat: int
    extras: Dict[str, int] = field(default_factory=dict)
    is_wicket: bool = False
    dismissal_type: Optional[DismissalType] = None
    is_boundary: bool = False
    is_six: bool = False

    @property
    def total_runs(self) -> int:
        return self.runs_off_bat + sum(self.extras.values())


@dataclass
class BallSimulationContext:
    """Context for simulating a single ball."""

    batting_team: TeamProfile
    bowling_team: TeamProfile
    over_number: int  # 0-19 for T20
    ball_in_over: int  # 1-6
    current_score: int
    wickets_fallen: int
    target: Optional[int] = None  # For second innings
    balls_remaining: int = 120


class MonteCarloSimulator:
    """
    Monte Carlo simulation engine for generating synthetic cricket matches.

    Uses probability distributions derived from team profiles to generate
    realistic ball-by-ball outcomes.
    """

    # Run scoring probabilities by phase (powerplay, middle, death)
    # Format: {runs: probability}
    BASE_RUN_PROBS = {
        "powerplay": {0: 0.30, 1: 0.35, 2: 0.12, 3: 0.02, 4: 0.12, 5: 0.01, 6: 0.08},
        "middle": {0: 0.32, 1: 0.38, 2: 0.10, 3: 0.02, 4: 0.10, 5: 0.01, 6: 0.07},
        "death": {0: 0.28, 1: 0.30, 2: 0.10, 3: 0.02, 4: 0.15, 5: 0.01, 6: 0.14},
    }

    # Wicket probability by phase per ball
    BASE_WICKET_PROBS = {
        "powerplay": 0.035,
        "middle": 0.040,
        "death": 0.055,
    }

    # Extra probability per ball
    EXTRA_PROBS = {
        "wides": 0.03,
        "noballs": 0.015,
        "byes": 0.01,
        "legbyes": 0.02,
    }

    # Dismissal type distribution
    DISMISSAL_PROBS = {
        DismissalType.CAUGHT: 0.55,
        DismissalType.BOWLED: 0.20,
        DismissalType.LBW: 0.12,
        DismissalType.RUN_OUT: 0.08,
        DismissalType.STUMPED: 0.04,
        DismissalType.HIT_WICKET: 0.005,
        DismissalType.CAUGHT_AND_BOWLED: 0.005,
    }

    def __init__(self, seed: Optional[int] = None):
        """Initialize simulator with optional random seed for reproducibility."""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def get_match_phase(self, over: int) -> str:
        """Determine match phase from over number."""
        if over < 6:
            return "powerplay"
        elif over < 16:
            return "middle"
        else:
            return "death"

    def adjust_run_probs(
        self,
        base_probs: Dict[int, float],
        batting_profile: TeamProfile,
        bowling_profile: TeamProfile,
        phase: str,
    ) -> Dict[int, float]:
        """
        Adjust run probabilities based on team profiles.
        """
        probs = base_probs.copy()

        # Get expected runs per over for each team in this phase
        if phase == "powerplay":
            bat_factor = batting_profile.avg_powerplay_runs / 50.0
            bowl_factor = 8.0 / bowling_profile.avg_powerplay_economy
        elif phase == "middle":
            bat_factor = batting_profile.avg_middle_overs_runs / 50.0
            bowl_factor = 8.0 / bowling_profile.avg_middle_economy
        else:
            bat_factor = batting_profile.avg_death_overs_runs / 50.0
            bowl_factor = 9.0 / bowling_profile.avg_death_economy

        # Combined factor (batting strength vs bowling strength)
        combined_factor = (bat_factor + bowl_factor) / 2.0

        # Aggressive batting style increases boundary probability
        if batting_profile.batting_style == BattingStyle.AGGRESSIVE:
            probs[4] *= 1.15
            probs[6] *= 1.20
            probs[0] *= 0.95
        elif batting_profile.batting_style == BattingStyle.DEFENSIVE:
            probs[1] *= 1.10
            probs[4] *= 0.90
            probs[6] *= 0.85

        # Apply volatility (higher volatility = more extreme outcomes)
        volatility = batting_profile.volatility
        probs[0] *= 1 + volatility * 0.1
        probs[6] *= 1 + volatility * 0.3

        # Normalize probabilities
        total = sum(probs.values())
        return {k: v / total for k, v in probs.items()}

    def adjust_wicket_prob(
        self,
        base_prob: float,
        batting_profile: TeamProfile,
        bowling_profile: TeamProfile,
        context: BallSimulationContext,
    ) -> float:
        """Adjust wicket probability based on context and team profiles."""
        prob = base_prob

        # Bowling team strength adjustment
        avg_wickets = bowling_profile.avg_wickets_per_match
        prob *= avg_wickets / 6.0  # Normalize to 6 wickets avg

        # Aggressive batting increases wicket risk
        if batting_profile.batting_style == BattingStyle.AGGRESSIVE:
            prob *= 1.10
        elif batting_profile.batting_style == BattingStyle.DEFENSIVE:
            prob *= 0.90

        # Volatility increases wicket risk
        prob *= 1 + batting_profile.volatility * 0.2

        # Spin bowling on middle overs is more effective
        phase = self.get_match_phase(context.over_number)
        if bowling_profile.bowling_strength == BowlingStrength.SPIN_DOMINANT:
            if phase == "middle":
                prob *= 1.15

        # Chasing pressure in second innings
        if context.target is not None:
            required_rate = (context.target - context.current_score) / (
                context.balls_remaining / 6
            )
            if required_rate > 12:
                prob *= 1.25  # High pressure increases wicket chance
            elif required_rate > 10:
                prob *= 1.10

        return min(0.15, prob)  # Cap at 15% per ball

    def simulate_delivery(self, context: BallSimulationContext) -> DeliveryOutcome:
        """Simulate a single delivery outcome."""
        phase = self.get_match_phase(context.over_number)

        # Check for extras first
        extras = {}
        is_legal_delivery = True

        for extra_type, prob in self.EXTRA_PROBS.items():
            if random.random() < prob:
                if extra_type == "wides":
                    extras["wides"] = random.choice([1, 2, 5])  # Wide can go for more
                    is_legal_delivery = False
                elif extra_type == "noballs":
                    extras["noballs"] = 1
                    is_legal_delivery = False
                elif extra_type in ["byes", "legbyes"]:
                    extras[extra_type] = random.choice([1, 2, 4])
                break  # Only one type of extra per ball

        # Adjust run probabilities
        run_probs = self.adjust_run_probs(
            self.BASE_RUN_PROBS[phase],
            context.batting_team,
            context.bowling_team,
            phase,
        )

        # Simulate runs
        runs_list = list(run_probs.keys())
        probs_list = list(run_probs.values())
        runs_off_bat = np.random.choice(runs_list, p=probs_list)

        # Check for wicket (only on legal deliveries and if runs == 0 or run out possible)
        is_wicket = False
        dismissal_type = None

        wicket_prob = self.adjust_wicket_prob(
            self.BASE_WICKET_PROBS[phase],
            context.batting_team,
            context.bowling_team,
            context,
        )

        # Wicket more likely on dot balls, but possible on any
        if runs_off_bat == 0:
            wicket_prob *= 1.5
        elif runs_off_bat in [1, 2, 3]:
            wicket_prob *= 0.3  # Run out possible
        else:
            wicket_prob *= 0.05  # Very rare on boundaries

        if context.wickets_fallen < 10 and random.random() < wicket_prob:
            is_wicket = True
            # Select dismissal type
            dismissal_types = list(self.DISMISSAL_PROBS.keys())
            dismissal_probs = list(self.DISMISSAL_PROBS.values())
            dismissal_type = np.random.choice(dismissal_types, p=dismissal_probs)

            # Run out only if running
            if runs_off_bat in [0, 4, 6] and dismissal_type == DismissalType.RUN_OUT:
                dismissal_type = DismissalType.CAUGHT

        return DeliveryOutcome(
            runs_off_bat=runs_off_bat,
            extras=extras,
            is_wicket=is_wicket,
            dismissal_type=dismissal_type,
            is_boundary=(runs_off_bat == 4),
            is_six=(runs_off_bat == 6),
        )

    def simulate_innings(
        self,
        batting_team: TeamProfile,
        bowling_team: TeamProfile,
        target: Optional[int] = None,
        max_overs: int = 20,
    ) -> Tuple[int, int, List[Dict]]:
        """
        Simulate a complete innings.

        Returns:
            Tuple of (total_runs, wickets, list of delivery dicts)
        """
        total_runs = 0
        wickets = 0
        deliveries = []
        balls_bowled = 0
        max_balls = max_overs * 6

        over = 0
        ball_in_over = 0

        while balls_bowled < max_balls and wickets < 10:
            # Check if target achieved (second innings)
            if target is not None and total_runs > target:
                break

            context = BallSimulationContext(
                batting_team=batting_team,
                bowling_team=bowling_team,
                over_number=over,
                ball_in_over=ball_in_over + 1,
                current_score=total_runs,
                wickets_fallen=wickets,
                target=target,
                balls_remaining=max_balls - balls_bowled,
            )

            outcome = self.simulate_delivery(context)

            # Record delivery
            delivery_record = {
                "over": over,
                "ball": ball_in_over + 1,
                "runs_off_bat": outcome.runs_off_bat,
                "extras": outcome.extras,
                "total_runs": outcome.total_runs,
                "is_wicket": outcome.is_wicket,
                "dismissal_type": (
                    outcome.dismissal_type.value if outcome.dismissal_type else None
                ),
                "is_boundary": outcome.is_boundary,
                "is_six": outcome.is_six,
            }
            deliveries.append(delivery_record)

            total_runs += outcome.total_runs

            if outcome.is_wicket:
                wickets += 1

            # Count legal deliveries
            if not outcome.extras.get("wides") and not outcome.extras.get("noballs"):
                ball_in_over += 1
                balls_bowled += 1

                if ball_in_over >= 6:
                    ball_in_over = 0
                    over += 1

        return total_runs, wickets, deliveries

    def simulate_match(
        self,
        team_a: TeamProfile,
        team_b: TeamProfile,
        venue: Optional[str] = None,
        date: Optional[datetime] = None,
    ) -> Dict:
        """
        Simulate a complete T20 match between two teams.

        Returns:
            Dict containing complete match data in Cricsheet-compatible format
        """
        if date is None:
            date = datetime.now()

        # Toss simulation
        toss_winner = random.choice([team_a, team_b])
        # Teams generally choose to chase in T20s
        toss_decision = "field" if random.random() < 0.65 else "bat"

        if toss_decision == "bat":
            batting_first = toss_winner
            batting_second = team_b if toss_winner == team_a else team_a
        else:
            batting_second = toss_winner
            batting_first = team_b if toss_winner == team_a else team_a

        # First innings
        first_innings_runs, first_innings_wickets, first_innings_deliveries = (
            self.simulate_innings(batting_first, batting_second)
        )

        # Second innings (chasing)
        target = first_innings_runs + 1
        second_innings_runs, second_innings_wickets, second_innings_deliveries = (
            self.simulate_innings(batting_second, batting_first, target=target)
        )

        # Determine winner
        if second_innings_runs >= target:
            winner = batting_second.name
            win_by = {"wickets": 10 - second_innings_wickets}
        else:
            winner = batting_first.name
            win_by = {"runs": first_innings_runs - second_innings_runs}

        # Construct match data
        match_data = {
            "meta": {
                "data_version": "1.0.0",
                "created": datetime.now().strftime("%Y-%m-%d"),
                "synthetic": True,
            },
            "info": {
                "balls_per_over": 6,
                "dates": [date.strftime("%Y-%m-%d")],
                "gender": "male",
                "match_type": "T20",
                "teams": [team_a.name, team_b.name],
                "toss": {
                    "winner": toss_winner.name,
                    "decision": toss_decision,
                },
                "outcome": {
                    "winner": winner,
                    "by": win_by,
                },
                "venue": venue or "Synthetic Venue",
                "overs": 20,
            },
            "innings": [
                {
                    "team": batting_first.name,
                    "overs": self._group_deliveries_by_over(first_innings_deliveries),
                    "total_runs": first_innings_runs,
                    "total_wickets": first_innings_wickets,
                },
                {
                    "team": batting_second.name,
                    "overs": self._group_deliveries_by_over(second_innings_deliveries),
                    "total_runs": second_innings_runs,
                    "total_wickets": second_innings_wickets,
                    "target": target,
                },
            ],
        }

        return match_data

    def _group_deliveries_by_over(self, deliveries: List[Dict]) -> List[Dict]:
        """Group deliveries by over number for Cricsheet format."""
        overs = {}
        for delivery in deliveries:
            over_num = delivery["over"]
            if over_num not in overs:
                overs[over_num] = {"over": over_num, "deliveries": []}

            # Format delivery for Cricsheet
            d = {
                "batter": f"Batter_{delivery['ball']}",  # Placeholder
                "bowler": f"Bowler_{over_num % 5 + 1}",  # Placeholder rotation
                "runs": {
                    "batter": delivery["runs_off_bat"],
                    "extras": sum(delivery["extras"].values()),
                    "total": delivery["total_runs"],
                },
            }

            if delivery["extras"]:
                d["extras"] = delivery["extras"]

            if delivery["is_wicket"]:
                d["wickets"] = [
                    {
                        "kind": delivery["dismissal_type"],
                        "player_out": f"Batter_{delivery['ball']}",
                    }
                ]

            overs[over_num]["deliveries"].append(d)

        return list(overs.values())

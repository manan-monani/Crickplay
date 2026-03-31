"""
Synthetic Match Data Generator

High-level interface for generating synthetic cricket match data.
Supports batch generation of matches for training ML models on
scenarios involving teams with limited historical data.
"""

import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from itertools import combinations

from .team_profiles import (
    TeamProfile,
    ESTABLISHED_TEAMS,
    EMERGING_TEAMS,
    ALL_TEAMS,
    get_team_profile,
    get_all_team_names,
)
from .monte_carlo import MonteCarloSimulator


class SyntheticMatchGenerator:
    """
    Generator for creating synthetic cricket match data.

    Designed to create realistic match scenarios for teams that
    don't have extensive historical data, particularly for upcoming
    tournaments like the 2026 World Cup.
    """

    # Common T20 World Cup venues
    VENUES = [
        "Melbourne Cricket Ground",
        "Sydney Cricket Ground",
        "Adelaide Oval",
        "Brisbane Cricket Ground",
        "Perth Stadium",
        "Narendra Modi Stadium",
        "Eden Gardens",
        "Wankhede Stadium",
        "Lord's Cricket Ground",
        "The Oval",
        "Dubai International Cricket Stadium",
        "Sheikh Zayed Stadium",
    ]

    def __init__(self, seed: Optional[int] = None, output_dir: Optional[str] = None):
        """
        Initialize the generator.

        Args:
            seed: Random seed for reproducibility
            output_dir: Directory to save generated matches
        """
        self.simulator = MonteCarloSimulator(seed=seed)
        self.output_dir = output_dir

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

    def generate_match(
        self,
        team_a_name: str,
        team_b_name: str,
        venue: Optional[str] = None,
        date: Optional[datetime] = None,
    ) -> Dict:
        """
        Generate a single synthetic match.

        Args:
            team_a_name: Name of first team
            team_b_name: Name of second team
            venue: Match venue (random if not specified)
            date: Match date (today if not specified)

        Returns:
            Match data dictionary in Cricsheet format
        """
        team_a = get_team_profile(team_a_name)
        team_b = get_team_profile(team_b_name)

        if team_a is None:
            raise ValueError(f"Unknown team: {team_a_name}")
        if team_b is None:
            raise ValueError(f"Unknown team: {team_b_name}")

        if venue is None:
            venue = random.choice(self.VENUES)

        if date is None:
            date = datetime.now()

        return self.simulator.simulate_match(team_a, team_b, venue, date)

    def generate_matchups_for_team(
        self,
        team_name: str,
        opponents: Optional[List[str]] = None,
        matches_per_opponent: int = 5,
        start_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Generate multiple matches for a specific team against various opponents.

        Useful for generating training data for a team with limited history.

        Args:
            team_name: Name of the focus team
            opponents: List of opponent names (all established teams if None)
            matches_per_opponent: Number of matches to generate per opponent
            start_date: Starting date for match generation

        Returns:
            List of generated match data
        """
        if opponents is None:
            opponents = list(ESTABLISHED_TEAMS.keys())

        if start_date is None:
            start_date = datetime.now()

        matches = []
        current_date = start_date

        for opponent in opponents:
            for i in range(matches_per_opponent):
                match_data = self.generate_match(
                    team_name,
                    opponent,
                    venue=random.choice(self.VENUES),
                    date=current_date,
                )

                # Add synthetic match ID
                match_data["info"][
                    "synthetic_match_id"
                ] = f"SYN_{team_name}_{opponent}_{i+1}_{current_date.strftime('%Y%m%d')}"

                matches.append(match_data)
                current_date += timedelta(days=random.randint(1, 7))

        return matches

    def generate_tournament_group_stage(
        self,
        group_teams: List[str],
        group_name: str = "A",
        start_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Generate all matches for a tournament group stage.

        Each team plays every other team once.

        Args:
            group_teams: List of team names in the group
            group_name: Name/letter of the group
            start_date: Tournament start date

        Returns:
            List of generated match data
        """
        if start_date is None:
            start_date = datetime.now()

        matches = []
        current_date = start_date

        # Generate all unique pairings
        matchups = list(combinations(group_teams, 2))

        for team_a, team_b in matchups:
            match_data = self.generate_match(
                team_a,
                team_b,
                date=current_date,
            )

            match_data["info"]["event"] = {
                "name": "2026 T20 World Cup (Synthetic)",
                "match_number": len(matches) + 1,
                "group": group_name,
            }

            matches.append(match_data)
            current_date += timedelta(days=random.randint(1, 3))

        return matches

    def generate_world_cup_2026_scenarios(
        self,
        scenarios_per_group: int = 3,
    ) -> Dict[str, List[Dict]]:
        """
        Generate synthetic World Cup 2026 group stage scenarios.

        Creates multiple possible tournament scenarios with emerging teams
        facing established nations.

        Args:
            scenarios_per_group: Number of complete group stage simulations

        Returns:
            Dict mapping group names to list of match data
        """
        # Example group configuration for 2026 World Cup
        groups = {
            "A": ["India", "Pakistan", "Ireland", "USA"],
            "B": ["England", "Australia", "Scotland", "Oman"],
            "C": ["New Zealand", "South Africa", "Nepal", "Canada"],
            "D": ["West Indies", "Bangladesh", "Netherlands", "Italy"],
        }

        all_scenarios = {}

        for group_name, teams in groups.items():
            group_matches = []

            for scenario in range(scenarios_per_group):
                start_date = datetime(2026, 6, 1) + timedelta(days=scenario * 15)
                scenario_matches = self.generate_tournament_group_stage(
                    teams, group_name, start_date
                )

                # Tag with scenario number
                for match in scenario_matches:
                    match["info"]["scenario_number"] = scenario + 1

                group_matches.extend(scenario_matches)

            all_scenarios[group_name] = group_matches

        return all_scenarios

    def save_matches_to_json(
        self,
        matches: List[Dict],
        output_dir: Optional[str] = None,
        prefix: str = "synthetic",
    ) -> List[str]:
        """
        Save generated matches to JSON files.

        Args:
            matches: List of match data dictionaries
            output_dir: Output directory (uses instance default if None)
            prefix: Filename prefix

        Returns:
            List of created file paths
        """
        save_dir = output_dir or self.output_dir
        if save_dir is None:
            raise ValueError("No output directory specified")

        os.makedirs(save_dir, exist_ok=True)

        file_paths = []

        for i, match in enumerate(matches):
            # Generate filename
            teams = match["info"]["teams"]
            date = match["info"]["dates"][0]
            filename = f"{prefix}_{teams[0]}_{teams[1]}_{date}_{i+1}.json"
            filename = filename.replace(" ", "_")

            file_path = os.path.join(save_dir, filename)

            with open(file_path, "w") as f:
                json.dump(match, f, indent=2)

            file_paths.append(file_path)

        return file_paths

    def get_match_statistics(self, match: Dict) -> Dict:
        """
        Extract key statistics from a generated match.

        Args:
            match: Match data dictionary

        Returns:
            Dictionary of match statistics
        """
        innings = match["innings"]

        stats = {
            "team_a": match["info"]["teams"][0],
            "team_b": match["info"]["teams"][1],
            "winner": match["info"]["outcome"]["winner"],
            "venue": match["info"]["venue"],
            "first_innings": {
                "team": innings[0]["team"],
                "total": innings[0]["total_runs"],
                "wickets": innings[0]["total_wickets"],
            },
            "second_innings": {
                "team": innings[1]["team"],
                "total": innings[1]["total_runs"],
                "wickets": innings[1]["total_wickets"],
                "target": innings[1].get("target"),
            },
        }

        # Calculate margin
        if "runs" in match["info"]["outcome"]["by"]:
            stats["margin"] = f"{match['info']['outcome']['by']['runs']} runs"
        else:
            stats["margin"] = f"{match['info']['outcome']['by']['wickets']} wickets"

        return stats


def main():
    """CLI entry point for generating synthetic data."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate synthetic cricket match data"
    )
    parser.add_argument(
        "--team",
        "-t",
        help="Generate matches for a specific team",
    )
    parser.add_argument(
        "--opponents",
        "-o",
        nargs="+",
        help="List of opponent teams",
    )
    parser.add_argument(
        "--matches",
        "-m",
        type=int,
        default=5,
        help="Number of matches per opponent (default: 5)",
    )
    parser.add_argument(
        "--world-cup",
        "-w",
        action="store_true",
        help="Generate World Cup 2026 scenarios",
    )
    parser.add_argument(
        "--output",
        "-O",
        default="src/storage/lakehouse/bronze/synthetic",
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--list-teams",
        action="store_true",
        help="List all available teams",
    )

    args = parser.parse_args()

    if args.list_teams:
        print("Established Teams:")
        for name in sorted(ESTABLISHED_TEAMS.keys()):
            print(f"  - {name}")
        print("\nEmerging Teams:")
        for name in sorted(EMERGING_TEAMS.keys()):
            print(f"  - {name}")
        return

    generator = SyntheticMatchGenerator(seed=args.seed, output_dir=args.output)

    if args.world_cup:
        print("Generating World Cup 2026 scenarios...")
        scenarios = generator.generate_world_cup_2026_scenarios()

        for group, matches in scenarios.items():
            print(f"\nGroup {group}: {len(matches)} matches generated")
            file_paths = generator.save_matches_to_json(
                matches, prefix=f"wc2026_group{group}"
            )
            print(f"  Saved to: {args.output}")

        total = sum(len(m) for m in scenarios.values())
        print(f"\nTotal matches generated: {total}")

    elif args.team:
        print(f"Generating matches for {args.team}...")
        matches = generator.generate_matchups_for_team(
            args.team,
            opponents=args.opponents,
            matches_per_opponent=args.matches,
        )

        file_paths = generator.save_matches_to_json(matches)
        print(f"Generated {len(matches)} matches")
        print(f"Saved to: {args.output}")

        # Print summary statistics
        wins = sum(1 for m in matches if m["info"]["outcome"]["winner"] == args.team)
        print(f"Win rate: {wins}/{len(matches)} ({100*wins/len(matches):.1f}%)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

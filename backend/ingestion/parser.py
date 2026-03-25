"""
Cricsheet JSON Parser
Parses ball-by-ball delivery data from Cricsheet JSON files
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional


@dataclass
class DeliveryEvent:
    """Represents a single ball/delivery in a cricket match."""

    # Match identification
    match_id: str
    match_date: str
    season: str
    event_name: str
    venue: str

    # Teams
    batting_team: str
    bowling_team: str
    teams: list[str]

    # Toss
    toss_winner: str
    toss_decision: str  # 'bat' or 'field'

    # Innings info
    innings_number: int  # 1 or 2
    over_number: int  # 0-19
    ball_number: int  # 1-6 (can be more for extras)

    # Players
    batter: str
    bowler: str
    non_striker: str

    # Runs
    batter_runs: int
    extra_runs: int
    total_runs: int

    # Extras breakdown (optional)
    extras_type: Optional[str] = None  # wides, noballs, byes, legbyes, penalty

    # Wicket info (optional)
    is_wicket: bool = False
    wicket_kind: Optional[str] = None  # bowled, caught, lbw, run out, etc.
    wicket_player_out: Optional[str] = None
    wicket_fielders: list[str] = field(default_factory=list)

    # Match context
    match_type: str = "T20"
    gender: str = "male"
    team_type: str = "international"

    # Outcome (filled after match ends)
    match_winner: Optional[str] = None
    win_margin: Optional[str] = None

    # Registry IDs
    batter_id: Optional[str] = None
    bowler_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "match_id": self.match_id,
            "match_date": self.match_date,
            "season": self.season,
            "event_name": self.event_name,
            "venue": self.venue,
            "batting_team": self.batting_team,
            "bowling_team": self.bowling_team,
            "teams": self.teams,
            "toss_winner": self.toss_winner,
            "toss_decision": self.toss_decision,
            "innings_number": self.innings_number,
            "over_number": self.over_number,
            "ball_number": self.ball_number,
            "batter": self.batter,
            "bowler": self.bowler,
            "non_striker": self.non_striker,
            "batter_runs": self.batter_runs,
            "extra_runs": self.extra_runs,
            "total_runs": self.total_runs,
            "extras_type": self.extras_type,
            "is_wicket": self.is_wicket,
            "wicket_kind": self.wicket_kind,
            "wicket_player_out": self.wicket_player_out,
            "wicket_fielders": self.wicket_fielders,
            "match_type": self.match_type,
            "gender": self.gender,
            "team_type": self.team_type,
            "match_winner": self.match_winner,
            "win_margin": self.win_margin,
            "batter_id": self.batter_id,
            "bowler_id": self.bowler_id,
        }


class CricsheetParser:
    """
    Parser for Cricsheet JSON match files.

    Yields DeliveryEvent objects for each ball in a match.
    Uses generator pattern to handle memory efficiently.
    """

    def __init__(self, data_dir: Path):
        """
        Initialize parser with data directory.

        Args:
            data_dir: Path to directory containing Cricsheet JSON files
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

    def list_matches(self) -> list[Path]:
        """List all JSON match files in the data directory."""
        return sorted(self.data_dir.glob("*.json"))

    def parse_match(self, match_file: Path) -> Generator[DeliveryEvent, None, None]:
        """
        Parse a single match file and yield DeliveryEvent objects.

        Args:
            match_file: Path to the match JSON file

        Yields:
            DeliveryEvent for each delivery in the match
        """
        with open(match_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract match info
        match_id = match_file.stem
        info = data.get("info", {})

        match_date = info.get("dates", ["unknown"])[0]
        season = info.get("season", "unknown")
        event = info.get("event", {})
        event_name = event.get("name", "unknown") if isinstance(event, dict) else str(event)
        venue = info.get("venue", "unknown")
        teams = info.get("teams", [])
        toss = info.get("toss", {})
        toss_winner = toss.get("winner", "unknown")
        toss_decision = toss.get("decision", "unknown")
        match_type = info.get("match_type", "T20")
        gender = info.get("gender", "male")
        team_type = info.get("team_type", "international")

        # Outcome
        outcome = info.get("outcome", {})
        match_winner = outcome.get("winner")
        win_by = outcome.get("by", {})
        if "runs" in win_by:
            win_margin = f"{win_by['runs']} runs"
        elif "wickets" in win_by:
            win_margin = f"{win_by['wickets']} wickets"
        else:
            win_margin = None

        # Player registry for IDs
        registry = info.get("registry", {}).get("people", {})

        # Parse innings
        innings_list = data.get("innings", [])

        for innings_idx, innings in enumerate(innings_list, start=1):
            batting_team = innings.get("team", "unknown")
            bowling_team = [t for t in teams if t != batting_team][0] if len(teams) == 2 else "unknown"

            overs = innings.get("overs", [])

            for over_data in overs:
                over_number = over_data.get("over", 0)
                deliveries = over_data.get("deliveries", [])

                for ball_idx, delivery in enumerate(deliveries, start=1):
                    # Extract delivery details
                    batter = delivery.get("batter", "unknown")
                    bowler = delivery.get("bowler", "unknown")
                    non_striker = delivery.get("non_striker", "unknown")

                    runs = delivery.get("runs", {})
                    batter_runs = runs.get("batter", 0)
                    extra_runs = runs.get("extras", 0)
                    total_runs = runs.get("total", 0)

                    # Extras
                    extras = delivery.get("extras", {})
                    extras_type = None
                    if extras:
                        extras_type = list(extras.keys())[0] if extras else None

                    # Wicket
                    wickets = delivery.get("wickets", [])
                    is_wicket = len(wickets) > 0
                    wicket_kind = None
                    wicket_player_out = None
                    wicket_fielders = []

                    if is_wicket:
                        wicket = wickets[0]  # Usually only one wicket per ball
                        wicket_kind = wicket.get("kind")
                        wicket_player_out = wicket.get("player_out")
                        fielders_data = wicket.get("fielders", [])
                        wicket_fielders = [
                            f.get("name", f) if isinstance(f, dict) else f
                            for f in fielders_data
                        ]

                    yield DeliveryEvent(
                        match_id=match_id,
                        match_date=match_date,
                        season=season,
                        event_name=event_name,
                        venue=venue,
                        batting_team=batting_team,
                        bowling_team=bowling_team,
                        teams=teams,
                        toss_winner=toss_winner,
                        toss_decision=toss_decision,
                        innings_number=innings_idx,
                        over_number=over_number,
                        ball_number=ball_idx,
                        batter=batter,
                        bowler=bowler,
                        non_striker=non_striker,
                        batter_runs=batter_runs,
                        extra_runs=extra_runs,
                        total_runs=total_runs,
                        extras_type=extras_type,
                        is_wicket=is_wicket,
                        wicket_kind=wicket_kind,
                        wicket_player_out=wicket_player_out,
                        wicket_fielders=wicket_fielders,
                        match_type=match_type,
                        gender=gender,
                        team_type=team_type,
                        match_winner=match_winner,
                        win_margin=win_margin,
                        batter_id=registry.get(batter),
                        bowler_id=registry.get(bowler),
                    )

    def parse_all_matches(
        self, limit: Optional[int] = None
    ) -> Generator[DeliveryEvent, None, None]:
        """
        Parse all match files and yield DeliveryEvent objects.

        Args:
            limit: Optional limit on number of matches to parse

        Yields:
            DeliveryEvent for each delivery across all matches
        """
        match_files = self.list_matches()

        if limit:
            match_files = match_files[:limit]

        for match_file in match_files:
            try:
                yield from self.parse_match(match_file)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing {match_file.name}: {e}")
                continue

    def get_match_summary(self, match_file: Path) -> dict:
        """
        Get a summary of a match (without ball-by-ball data).

        Args:
            match_file: Path to the match JSON file

        Returns:
            Dictionary with match summary
        """
        with open(match_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        info = data.get("info", {})
        outcome = info.get("outcome", {})

        return {
            "match_id": match_file.stem,
            "date": info.get("dates", ["unknown"])[0],
            "venue": info.get("venue", "unknown"),
            "teams": info.get("teams", []),
            "toss_winner": info.get("toss", {}).get("winner"),
            "toss_decision": info.get("toss", {}).get("decision"),
            "winner": outcome.get("winner"),
            "player_of_match": info.get("player_of_match", []),
            "match_type": info.get("match_type", "T20"),
            "event": info.get("event", {}),
        }


if __name__ == "__main__":
    # Example usage
    from pathlib import Path

    data_dir = Path(__file__).parent.parent.parent / "data" / "raw" / "t20s_json"

    if data_dir.exists():
        parser = CricsheetParser(data_dir)
        matches = parser.list_matches()
        print(f"Found {len(matches)} match files")

        # Parse first match
        if matches:
            first_match = matches[0]
            print(f"\nParsing {first_match.name}...")

            summary = parser.get_match_summary(first_match)
            print(f"Match: {summary['teams'][0]} vs {summary['teams'][1]}")
            print(f"Venue: {summary['venue']}")
            print(f"Winner: {summary['winner']}")

            # Count deliveries
            delivery_count = sum(1 for _ in parser.parse_match(first_match))
            print(f"Total deliveries: {delivery_count}")
    else:
        print(f"Data directory not found: {data_dir}")

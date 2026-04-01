"""
Gold Layer - Star Schema Implementation

Business-ready data layer with dimensional Star Schema optimized for:
- BI visualization and dashboards
- ML feature extraction
- Analytics queries

Fact Tables:
- fact_delivery: One row per ball with metrics
- fact_match_summary: Aggregated match-level metrics

Dimension Tables:
- dim_player: Player attributes and styles
- dim_venue: Venue characteristics and history
- dim_match_context: Match conditions and metadata
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    pa = None
    pq = None


@dataclass
class GoldConfig:
    """Configuration for Gold layer processing."""

    silver_path: str = "src/storage/lakehouse/silver"
    gold_path: str = "src/storage/lakehouse/gold"

    output_format: str = "parquet"
    compression: str = "snappy"


# === DIMENSION TABLE SCHEMAS ===


@dataclass
class DimDate:
    """Date dimension for time-based analysis (date spine)."""
    
    date_key: str  # Primary key (YYYY-MM-DD format)
    full_date: str
    year: int
    month: int
    day: int
    day_of_week: int  # 0=Monday, 6=Sunday
    day_name: str  # Monday, Tuesday, etc.
    is_weekend: bool
    quarter: int
    week_of_year: int
    
    # Tournament-specific
    tournament_week_number: Optional[int] = None
    tournament_phase: Optional[str] = None  # Group, Super8, Semifinal, Final
    
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class DimPlayer:
    """Player dimension record."""

    player_id: str  # Primary key (canonical ID)
    player_name: str  # Most common name
    alternative_names: str  # JSON array of aliases
    batting_style: Optional[str] = None  # right-hand, left-hand
    bowling_style: Optional[str] = None  # right-arm fast, left-arm spin, etc.
    primary_role: Optional[str] = None  # batter, bowler, all-rounder
    nationality: Optional[str] = None

    # Aggregated career stats (updated incrementally)
    total_matches: int = 0
    total_runs_scored: int = 0
    total_wickets_taken: int = 0
    total_balls_faced: int = 0
    total_balls_bowled: int = 0

    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.utcnow().isoformat()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now


@dataclass
class DimVenue:
    """Venue dimension record."""

    venue_id: str  # Primary key
    venue_name: str
    city: Optional[str] = None
    country: Optional[str] = None

    # Venue characteristics
    pitch_type: Optional[str] = None  # batting, bowling, spin-friendly, pace-friendly
    boundary_size: Optional[str] = None  # small, medium, large
    avg_first_innings_score: Optional[float] = None
    avg_second_innings_score: Optional[float] = None

    # Historical stats
    total_matches: int = 0
    total_runs: int = 0

    created_at: str = ""
    updated_at: str = ""


@dataclass
class DimMatchContext:
    """Match context dimension record."""

    match_context_id: str  # Primary key
    match_id: str
    match_type: str  # T20, ODI, Test
    match_date: str
    venue_id: str

    # Teams
    team_a: str
    team_b: str

    # Toss
    toss_winner: Optional[str] = None
    toss_decision: Optional[str] = None  # bat, field

    # Conditions (can be enriched with external data)
    weather: Optional[str] = None
    day_night: Optional[str] = None  # day, day-night, night

    # Outcome
    winner: Optional[str] = None
    win_margin: Optional[str] = None
    player_of_match: Optional[str] = None

    created_at: str = ""


# === FACT TABLE SCHEMAS ===


@dataclass
class FactDelivery:
    """Delivery fact record (grain: one row per ball)."""

    delivery_key: str  # Surrogate key

    # Foreign keys
    match_context_id: str
    batter_id: str
    bowler_id: str
    venue_id: str

    # Delivery position
    inning: int
    over: int
    ball: int

    # Measures
    runs_batter: int
    runs_extras: int
    runs_total: int

    # Extras breakdown
    wides: int = 0
    noballs: int = 0
    byes: int = 0
    legbyes: int = 0

    # Flags
    is_legal_delivery: bool = True
    is_four: bool = False
    is_six: bool = False
    is_wicket: bool = False
    is_dot_ball: bool = False

    # Wicket details (denormalized for query performance)
    wicket_kind: Optional[str] = None

    # ML/Analytics fields
    win_probability_delta: float = 0.0  # Change in win probability after this delivery

    # Multi-tenancy support (RLS)
    tenant_id: Optional[str] = None

    # Timestamps
    event_timestamp: str = ""


@dataclass
class FactMatchSummary:
    """Match summary fact record (grain: one row per match)."""

    match_key: str  # Surrogate key

    # Foreign keys
    match_context_id: str
    venue_id: str

    # First innings (required fields)
    first_innings_team: str
    first_innings_runs: int
    first_innings_wickets: int
    first_innings_balls: int

    # Second innings (required fields)
    second_innings_team: str
    second_innings_runs: int
    second_innings_wickets: int
    second_innings_balls: int

    # First innings (optional fields with defaults)
    first_innings_fours: int = 0
    first_innings_sixes: int = 0
    first_innings_extras: int = 0

    # Second innings (optional fields with defaults)
    second_innings_fours: int = 0
    second_innings_sixes: int = 0
    second_innings_extras: int = 0

    # Match aggregates
    total_runs: int = 0
    total_wickets: int = 0
    total_fours: int = 0
    total_sixes: int = 0
    total_extras: int = 0

    # Derived metrics
    run_rate_first: float = 0.0
    run_rate_second: float = 0.0
    win_margin: Optional[str] = None

    # Multi-tenancy support (RLS)
    tenant_id: Optional[str] = None

    created_at: str = ""


class StarSchemaBuilder:
    """
    Builds Star Schema from Silver layer data.

    Handles:
    - Dimension table population
    - Fact table aggregation
    - Incremental updates
    - Surrogate key generation
    """

    def __init__(self, config: Optional[GoldConfig] = None):
        self.config = config or GoldConfig()

        # In-memory dimension caches
        self._players: Dict[str, DimPlayer] = {}
        self._venues: Dict[str, DimVenue] = {}
        self._match_contexts: Dict[str, DimMatchContext] = {}
        self._dates: Dict[str, DimDate] = {}

        # Fact accumulator
        self._deliveries: List[FactDelivery] = []
        self._match_summaries: Dict[str, Dict] = {}  # match_id -> running totals

        # Ensure output directories
        os.makedirs(os.path.join(self.config.gold_path, "dim_player"), exist_ok=True)
        os.makedirs(os.path.join(self.config.gold_path, "dim_venue"), exist_ok=True)
        os.makedirs(os.path.join(self.config.gold_path, "dim_date"), exist_ok=True)
        os.makedirs(
            os.path.join(self.config.gold_path, "dim_match_context"), exist_ok=True
        )
        os.makedirs(os.path.join(self.config.gold_path, "fact_delivery"), exist_ok=True)
        os.makedirs(
            os.path.join(self.config.gold_path, "fact_match_summary"), exist_ok=True
        )

        self._load_existing_dimensions()

    def _load_existing_dimensions(self) -> None:
        """Load existing dimension data from Gold layer."""
        # Load players
        player_path = os.path.join(self.config.gold_path, "dim_player")
        for f in os.listdir(player_path) if os.path.exists(player_path) else []:
            if f.endswith(".json"):
                with open(os.path.join(player_path, f)) as file:
                    for record in json.load(file):
                        self._players[record["player_id"]] = DimPlayer(**record)

        # Load venues
        venue_path = os.path.join(self.config.gold_path, "dim_venue")
        for f in os.listdir(venue_path) if os.path.exists(venue_path) else []:
            if f.endswith(".json"):
                with open(os.path.join(venue_path, f)) as file:
                    for record in json.load(file):
                        self._venues[record["venue_id"]] = DimVenue(**record)

    def _generate_venue_id(self, venue_name: str) -> str:
        """Generate venue ID from name."""
        return hashlib.md5(venue_name.lower().encode()).hexdigest()[:12]

    def _generate_delivery_key(
        self, match_id: str, inning: int, over: int, ball: int
    ) -> str:
        """Generate surrogate key for delivery."""
        return f"{match_id}_{inning}_{over}_{ball}"

    def ensure_player(self, player_id: str, player_name: str) -> DimPlayer:
        """Ensure player exists in dimension table."""
        if player_id not in self._players:
            self._players[player_id] = DimPlayer(
                player_id=player_id,
                player_name=player_name,
                alternative_names=json.dumps([player_name]),
            )
        return self._players[player_id]

    def ensure_venue(self, venue_name: str) -> DimVenue:
        """Ensure venue exists in dimension table."""
        venue_id = self._generate_venue_id(venue_name)

        if venue_id not in self._venues:
            self._venues[venue_id] = DimVenue(
                venue_id=venue_id,
                venue_name=venue_name,
            )
        return self._venues[venue_id]

    def ensure_match_context(self, silver_record: Dict) -> DimMatchContext:
        """Ensure match context exists in dimension table."""
        match_id = silver_record.get("match_id", "unknown")

        if match_id not in self._match_contexts:
            venue = self.ensure_venue(silver_record.get("venue", "Unknown"))

            self._match_contexts[match_id] = DimMatchContext(
                match_context_id=match_id,
                match_id=match_id,
                match_type=silver_record.get("match_type", "T20"),
                match_date=silver_record.get("match_date", ""),
                venue_id=venue.venue_id,
                team_a=silver_record.get("inning", ""),
                team_b="",  # Will be filled from other records
            )

        return self._match_contexts[match_id]

    def ensure_date(self, date_str: str) -> DimDate:
        """Ensure date exists in dimension table (date spine)."""
        if not date_str:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        date_key = date_str[:10]  # YYYY-MM-DD
        
        if date_key not in self._dates:
            try:
                dt = datetime.strptime(date_key, "%Y-%m-%d")
            except ValueError:
                dt = datetime.utcnow()
                date_key = dt.strftime("%Y-%m-%d")
            
            self._dates[date_key] = DimDate(
                date_key=date_key,
                full_date=dt.strftime("%B %d, %Y"),
                year=dt.year,
                month=dt.month,
                day=dt.day,
                day_of_week=dt.weekday(),
                day_name=dt.strftime("%A"),
                is_weekend=dt.weekday() >= 5,
                quarter=(dt.month - 1) // 3 + 1,
                week_of_year=dt.isocalendar()[1],
            )
        
        return self._dates[date_key]

    def process_silver_record(self, record: Dict) -> None:
        """Process a single Silver layer record into Gold layer."""
        # Ensure dimensions exist
        batter = self.ensure_player(
            record.get("batter_id", "unknown"),
            record.get("batter_name", "Unknown"),
        )
        bowler = self.ensure_player(
            record.get("bowler_id", "unknown"),
            record.get("bowler_name", "Unknown"),
        )
        venue = self.ensure_venue(record.get("venue", "Unknown"))
        match_context = self.ensure_match_context(record)

        # Update player stats
        batter.total_balls_faced += 1 if record.get("is_legal_delivery", True) else 0
        batter.total_runs_scored += record.get("runs_batter", 0)
        bowler.total_balls_bowled += 1 if record.get("is_legal_delivery", True) else 0
        if record.get("is_wicket", False):
            bowler.total_wickets_taken += 1

        # Create fact delivery
        delivery = FactDelivery(
            delivery_key=self._generate_delivery_key(
                record.get("match_id", ""),
                1,  # inning number - would need to derive
                record.get("over", 0),
                record.get("ball", 0),
            ),
            match_context_id=match_context.match_context_id,
            batter_id=batter.player_id,
            bowler_id=bowler.player_id,
            venue_id=venue.venue_id,
            inning=1,  # Simplified - would need actual inning tracking
            over=record.get("over", 0),
            ball=record.get("ball", 0),
            runs_batter=record.get("runs_batter", 0),
            runs_extras=record.get("runs_extras", 0),
            runs_total=record.get("runs_total", 0),
            wides=record.get("wides", 0),
            noballs=record.get("noballs", 0),
            byes=record.get("byes", 0),
            legbyes=record.get("legbyes", 0),
            is_legal_delivery=record.get("is_legal_delivery", True),
            is_four=record.get("is_four", False),
            is_six=record.get("is_six", False),
            is_wicket=record.get("is_wicket", False),
            is_dot_ball=record.get("runs_total", 0) == 0
            and not record.get("is_wicket", False),
            wicket_kind=record.get("wicket_kind"),
            event_timestamp=record.get("ingestion_timestamp", ""),
        )

        self._deliveries.append(delivery)

        # Update match summary accumulator
        match_id = record.get("match_id", "")
        if match_id not in self._match_summaries:
            self._match_summaries[match_id] = {
                "first_innings_runs": 0,
                "first_innings_wickets": 0,
                "first_innings_balls": 0,
                "first_innings_fours": 0,
                "first_innings_sixes": 0,
                "first_innings_extras": 0,
                "total_deliveries": 0,
            }

        summary = self._match_summaries[match_id]
        summary["first_innings_runs"] += record.get("runs_total", 0)
        summary["first_innings_wickets"] += 1 if record.get("is_wicket", False) else 0
        summary["first_innings_balls"] += (
            1 if record.get("is_legal_delivery", True) else 0
        )
        summary["first_innings_fours"] += 1 if record.get("is_four", False) else 0
        summary["first_innings_sixes"] += 1 if record.get("is_six", False) else 0
        summary["first_innings_extras"] += record.get("runs_extras", 0)
        summary["total_deliveries"] += 1

    def read_silver_files(self) -> List[Dict]:
        """Read all Silver layer data."""
        records = []

        for root, dirs, files in os.walk(self.config.silver_path):
            for filename in files:
                file_path = os.path.join(root, filename)

                try:
                    if filename.endswith(".parquet") and pq is not None:
                        table = pq.read_table(file_path)
                        for i in range(table.num_rows):
                            row = {
                                col: table.column(col)[i].as_py()
                                for col in table.column_names
                            }
                            records.append(row)

                    elif filename.endswith(".csv") and pd is not None:
                        df = pd.read_csv(file_path)
                        records.extend(df.to_dict("records"))

                    elif filename.endswith(".json"):
                        with open(file_path) as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                records.extend(data)
                            else:
                                records.append(data)

                except Exception as e:
                    print(f"[Gold] Error reading {file_path}: {e}")

        return records

    def build(self) -> Dict[str, int]:
        """
        Build Gold layer from Silver layer data.

        Returns:
            Dict with counts of records written per table
        """
        print("[Gold] Reading Silver layer data...")
        records = self.read_silver_files()

        if not records:
            print("[Gold] No Silver layer data found")
            return {}

        print(f"[Gold] Processing {len(records)} records...")
        for record in records:
            self.process_silver_record(record)

        print("[Gold] Writing dimension tables...")
        self._write_dimensions()

        print("[Gold] Writing fact tables...")
        self._write_facts()

        return {
            "dim_player": len(self._players),
            "dim_venue": len(self._venues),
            "dim_match_context": len(self._match_contexts),
            "fact_delivery": len(self._deliveries),
            "fact_match_summary": len(self._match_summaries),
        }

    def _write_dimensions(self) -> None:
        """Write dimension tables to Gold layer."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Write dim_player
        if self._players:
            player_records = [asdict(p) for p in self._players.values()]
            self._write_table(
                player_records,
                os.path.join(
                    self.config.gold_path, "dim_player", f"players_{timestamp}.json"
                ),
            )

        # Write dim_venue
        if self._venues:
            venue_records = [asdict(v) for v in self._venues.values()]
            self._write_table(
                venue_records,
                os.path.join(
                    self.config.gold_path, "dim_venue", f"venues_{timestamp}.json"
                ),
            )

        # Write dim_match_context
        if self._match_contexts:
            context_records = [asdict(c) for c in self._match_contexts.values()]
            self._write_table(
                context_records,
                os.path.join(
                    self.config.gold_path,
                    "dim_match_context",
                    f"contexts_{timestamp}.json",
                ),
            )

    def _write_facts(self) -> None:
        """Write fact tables to Gold layer."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Write fact_delivery
        if self._deliveries:
            delivery_records = [asdict(d) for d in self._deliveries]

            if self.config.output_format == "parquet" and pa is not None:
                path = os.path.join(
                    self.config.gold_path,
                    "fact_delivery",
                    f"deliveries_{timestamp}.parquet",
                )
                table = pa.Table.from_pylist(delivery_records)
                pq.write_table(table, path, compression=self.config.compression)
            else:
                path = os.path.join(
                    self.config.gold_path,
                    "fact_delivery",
                    f"deliveries_{timestamp}.json",
                )
                self._write_table(delivery_records, path)

        # Write fact_match_summary
        if self._match_summaries:
            summary_records = []
            for match_id, summary in self._match_summaries.items():
                context = self._match_contexts.get(match_id)
                venue = self._venues.get(context.venue_id) if context else None

                summary_records.append(
                    {
                        "match_key": match_id,
                        "match_context_id": match_id,
                        "venue_id": venue.venue_id if venue else "",
                        "first_innings_team": context.team_a if context else "",
                        "first_innings_runs": summary["first_innings_runs"],
                        "first_innings_wickets": summary["first_innings_wickets"],
                        "first_innings_balls": summary["first_innings_balls"],
                        "first_innings_fours": summary["first_innings_fours"],
                        "first_innings_sixes": summary["first_innings_sixes"],
                        "first_innings_extras": summary["first_innings_extras"],
                        "second_innings_team": "",
                        "second_innings_runs": 0,
                        "second_innings_wickets": 0,
                        "second_innings_balls": 0,
                        "total_runs": summary["first_innings_runs"],
                        "total_wickets": summary["first_innings_wickets"],
                        "total_fours": summary["first_innings_fours"],
                        "total_sixes": summary["first_innings_sixes"],
                        "run_rate_first": (
                            summary["first_innings_runs"]
                            / (summary["first_innings_balls"] / 6)
                            if summary["first_innings_balls"] > 0
                            else 0
                        ),
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )

            path = os.path.join(
                self.config.gold_path,
                "fact_match_summary",
                f"summaries_{timestamp}.json",
            )
            self._write_table(summary_records, path)

    def _write_table(self, records: List[Dict], path: str) -> None:
        """Write records to file."""
        with open(path, "w") as f:
            json.dump(records, f, indent=2)
        print(f"[Gold] Wrote {len(records)} records to {path}")

    def get_statistics(self) -> Dict:
        """Get Gold layer statistics."""
        stats = {
            "dim_player_count": len(self._players),
            "dim_venue_count": len(self._venues),
            "dim_match_context_count": len(self._match_contexts),
            "fact_delivery_count": len(self._deliveries),
            "fact_match_summary_count": len(self._match_summaries),
        }

        # Count files on disk
        for table in [
            "dim_player",
            "dim_venue",
            "dim_match_context",
            "fact_delivery",
            "fact_match_summary",
        ]:
            table_path = os.path.join(self.config.gold_path, table)
            if os.path.exists(table_path):
                files = [
                    f
                    for f in os.listdir(table_path)
                    if f.endswith((".parquet", ".json"))
                ]
                stats[f"{table}_files"] = len(files)

        return stats


def main():
    """CLI entry point for Gold layer operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Gold Layer Star Schema Builder")
    parser.add_argument(
        "--mode",
        "-m",
        choices=["build", "stats"],
        default="build",
        help="Operation mode",
    )
    parser.add_argument(
        "--silver-path",
        default="src/storage/lakehouse/silver",
        help="Silver layer path",
    )
    parser.add_argument(
        "--gold-path",
        default="src/storage/lakehouse/gold",
        help="Gold layer path",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["parquet", "json"],
        default="parquet",
        help="Output format for fact tables",
    )

    args = parser.parse_args()

    config = GoldConfig(
        silver_path=args.silver_path,
        gold_path=args.gold_path,
        output_format=args.format,
    )

    builder = StarSchemaBuilder(config)

    if args.mode == "build":
        counts = builder.build()
        print("\n[Gold] Build complete:")
        for table, count in counts.items():
            print(f"  {table}: {count} records")

    elif args.mode == "stats":
        stats = builder.get_statistics()
        print("Gold Layer Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()

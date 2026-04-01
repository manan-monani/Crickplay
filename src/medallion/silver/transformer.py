"""
Silver Layer - ELT Transformer

Transforms raw Bronze layer data into cleansed, conformed tabular format.

Key Features:
- JSON flattening: Unnest nested delivery arrays into relational format
- Player identity standardization: Map to canonical Cricsheet IDs
- Cricket-specific null handling: extras=null means legal delivery
- Data type casting: String→INT for runs, ISO 8601 for dates
- Change Data Capture (CDC): Only process new/modified data

CDC Integration:
    The transformer uses the centralized CDC system (src/medallion/cdc.py)
    for tracking processed files and preventing duplicate records:
    
    ```python
    from src.medallion.cdc import CDCManager
    
    transformer = SilverTransformer(use_enhanced_cdc=True)
    files, records = transformer.run_incremental()
    ```

Architecture:
    Bronze (Parquet) → Silver Transformer → Silver (Parquet)
    
    - File-level CDC: Track which Bronze files have been transformed
    - Record-level dedup: Hash-based duplicate detection
    - Watermark tracking: Timestamp-based incremental queries
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Generator
from dataclasses import dataclass, field
from pathlib import Path

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

# Import enhanced CDC system
try:
    from src.medallion.cdc import CDCManager, CDCConfig
    CDC_AVAILABLE = True
except ImportError:
    CDC_AVAILABLE = False


@dataclass
class SilverConfig:
    """Configuration for Silver layer processing."""

    bronze_path: str = "src/storage/lakehouse/bronze"
    silver_path: str = "src/storage/lakehouse/silver"

    # CDC tracking
    checkpoint_file: str = "src/storage/lakehouse/silver/.checkpoint"

    # Output format
    output_format: str = "parquet"  # parquet or csv
    compression: str = "snappy"


class PlayerIdentityMapper:
    """
    Maps various player name representations to canonical identifiers.

    Cricket data often has inconsistent player naming:
    - "V Kohli" vs "Virat Kohli" vs "V. Kohli"
    - Different transliterations for non-English names
    """

    # Known aliases (expandable)
    ALIASES: Dict[str, str] = {
        # Indian players
        "V Kohli": "virat_kohli",
        "Virat Kohli": "virat_kohli",
        "V. Kohli": "virat_kohli",
        "MS Dhoni": "ms_dhoni",
        "M.S. Dhoni": "ms_dhoni",
        "MS Dhoni (wk)": "ms_dhoni",
        "Mahendra Singh Dhoni": "ms_dhoni",
        "R Sharma": "rohit_sharma",
        "RG Sharma": "rohit_sharma",
        "Rohit Sharma": "rohit_sharma",
        "JJ Bumrah": "jasprit_bumrah",
        "Jasprit Bumrah": "jasprit_bumrah",
        # Australian players
        "SPD Smith": "steve_smith",
        "Steve Smith": "steve_smith",
        "S Smith": "steve_smith",
        "DA Warner": "david_warner",
        "David Warner": "david_warner",
        "D Warner": "david_warner",
        "PJ Cummins": "pat_cummins",
        "Pat Cummins": "pat_cummins",
        # English players
        "JE Root": "joe_root",
        "Joe Root": "joe_root",
        "BA Stokes": "ben_stokes",
        "Ben Stokes": "ben_stokes",
        # More can be added from registry data
    }

    def __init__(self):
        self._cache: Dict[str, str] = {}

    def get_canonical_id(self, name: str, registry_id: Optional[str] = None) -> str:
        """
        Get canonical player ID from name.

        Uses registry ID if available, otherwise matches known aliases
        or generates a normalized ID.
        """
        if registry_id:
            return registry_id

        if name in self._cache:
            return self._cache[name]

        # Check known aliases
        if name in self.ALIASES:
            canonical = self.ALIASES[name]
            self._cache[name] = canonical
            return canonical

        # Generate normalized ID
        normalized = self._normalize_name(name)
        self._cache[name] = normalized
        return normalized

    def _normalize_name(self, name: str) -> str:
        """Normalize a player name to a canonical ID."""
        # Remove special characters, lowercase, replace spaces with underscore
        normalized = name.lower()
        normalized = normalized.replace(".", "")
        normalized = normalized.replace("(wk)", "").replace("(c)", "")
        normalized = normalized.strip()
        normalized = "_".join(normalized.split())
        return normalized

    def add_alias(self, alias: str, canonical_id: str) -> None:
        """Add a new alias mapping."""
        self.ALIASES[alias] = canonical_id
        self._cache[alias] = canonical_id


class DeliveryFlattener:
    """
    Flattens nested Cricsheet JSON delivery data into tabular format.
    """

    def __init__(self, player_mapper: Optional[PlayerIdentityMapper] = None):
        self.player_mapper = player_mapper or PlayerIdentityMapper()

    def flatten_delivery(
        self,
        raw_payload: Dict,
        registry: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """
        Flatten a single delivery from raw payload.

        Args:
            raw_payload: Raw message from Bronze layer
            registry: Optional player registry mapping

        Returns:
            Flattened dictionary with standardized columns
        """
        delivery = raw_payload.get("delivery_details", {})
        match_context = raw_payload.get("match_context", {})

        # Extract runs
        runs_data = delivery.get("runs", {})
        if isinstance(runs_data, dict):
            runs_batter = runs_data.get("batter", 0)
            runs_extras = runs_data.get("extras", 0)
            runs_total = runs_data.get("total", runs_batter + runs_extras)
        else:
            runs_batter = runs_data if isinstance(runs_data, int) else 0
            runs_extras = 0
            runs_total = runs_batter

        # Extract extras detail
        extras = delivery.get("extras", {})
        # Handle cricket-specific nulls: no extras object = legal delivery
        wides = extras.get("wides", 0) if extras else 0
        noballs = extras.get("noballs", 0) if extras else 0
        byes = extras.get("byes", 0) if extras else 0
        legbyes = extras.get("legbyes", 0) if extras else 0
        penalty = extras.get("penalty", 0) if extras else 0

        # Legal delivery indicator
        is_legal = (wides == 0) and (noballs == 0)

        # Extract wicket info
        wickets = delivery.get("wickets", [])
        is_wicket = len(wickets) > 0
        wicket_kind = wickets[0].get("kind") if is_wicket else None
        player_out = wickets[0].get("player_out") if is_wicket else None

        # Get player IDs
        batter_name = delivery.get("batter", "")
        bowler_name = delivery.get("bowler", "")
        non_striker_name = delivery.get("non_striker", "")

        batter_id = self.player_mapper.get_canonical_id(
            batter_name,
            registry.get(batter_name) if registry else None,
        )
        bowler_id = self.player_mapper.get_canonical_id(
            bowler_name,
            registry.get(bowler_name) if registry else None,
        )

        # Build flattened record
        return {
            # Match identifiers
            "match_id": match_context.get("file_id", "unknown"),
            "match_type": match_context.get("match_type"),
            "venue": match_context.get("venue"),
            "match_date": match_context.get("date"),
            # Delivery position
            "inning": raw_payload.get("inning_team"),
            "over": raw_payload.get("over"),
            "ball": raw_payload.get("ball"),
            "delivery_id": f"{match_context.get('file_id', '')}_{raw_payload.get('over', 0)}_{raw_payload.get('ball', 0)}",
            # Players (normalized)
            "batter_name": batter_name,
            "batter_id": batter_id,
            "bowler_name": bowler_name,
            "bowler_id": bowler_id,
            "non_striker_name": non_striker_name,
            # Runs
            "runs_batter": runs_batter,
            "runs_extras": runs_extras,
            "runs_total": runs_total,
            # Extras breakdown
            "wides": wides,
            "noballs": noballs,
            "byes": byes,
            "legbyes": legbyes,
            "penalty": penalty,
            "is_legal_delivery": is_legal,
            # Boundaries
            "is_four": runs_batter == 4 and runs_extras == 0,
            "is_six": runs_batter == 6,
            # Wickets
            "is_wicket": is_wicket,
            "wicket_kind": wicket_kind,
            "player_out": player_out,
            # Timestamps
            "ingestion_timestamp": raw_payload.get("ingestion_timestamp"),
            "silver_timestamp": datetime.utcnow().isoformat(),
        }


class ChangeDataCapture:
    """
    Tracks processed files to enable incremental processing.

    Maintains a checkpoint of:
    - Last processed timestamp
    - Set of processed file hashes
    """

    def __init__(self, checkpoint_file: str):
        self.checkpoint_file = checkpoint_file
        self._processed_files: Set[str] = set()
        self._last_processed: Optional[datetime] = None

        self._load_checkpoint()

    def _load_checkpoint(self) -> None:
        """Load checkpoint from disk."""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, "r") as f:
                data = json.load(f)
                self._processed_files = set(data.get("processed_files", []))
                last = data.get("last_processed")
                if last:
                    self._last_processed = datetime.fromisoformat(last)

    def _save_checkpoint(self) -> None:
        """Save checkpoint to disk."""
        os.makedirs(os.path.dirname(self.checkpoint_file), exist_ok=True)

        with open(self.checkpoint_file, "w") as f:
            json.dump(
                {
                    "processed_files": list(self._processed_files),
                    "last_processed": (
                        self._last_processed.isoformat()
                        if self._last_processed
                        else None
                    ),
                    "checkpoint_time": datetime.utcnow().isoformat(),
                },
                f,
                indent=2,
            )

    def get_file_hash(self, file_path: str) -> str:
        """Get hash of file for deduplication."""
        return hashlib.md5(file_path.encode()).hexdigest()

    def is_processed(self, file_path: str) -> bool:
        """Check if a file has already been processed."""
        return self.get_file_hash(file_path) in self._processed_files

    def mark_processed(self, file_path: str) -> None:
        """Mark a file as processed."""
        self._processed_files.add(self.get_file_hash(file_path))
        self._last_processed = datetime.utcnow()

    def commit(self) -> None:
        """Commit checkpoint to disk."""
        self._save_checkpoint()

    def reset(self) -> None:
        """Reset checkpoint (reprocess everything)."""
        self._processed_files.clear()
        self._last_processed = None
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)


class SilverTransformer:
    """
    Main Silver layer transformer.

    Orchestrates the ELT process:
    1. Extract: Read new data from Bronze layer
    2. Load: Load into processing pipeline
    3. Transform: Flatten, cleanse, standardize

    CDC Integration:
        Supports both legacy CDC (ChangeDataCapture class) and enhanced CDC
        (CDCManager from src/medallion/cdc.py). Use `use_enhanced_cdc=True`
        for production deployments.
    """

    def __init__(
        self,
        config: Optional[SilverConfig] = None,
        use_enhanced_cdc: bool = False,
    ):
        self.config = config or SilverConfig()
        self.flattener = DeliveryFlattener()
        
        # Choose CDC implementation
        self._use_enhanced_cdc = use_enhanced_cdc and CDC_AVAILABLE
        
        if self._use_enhanced_cdc:
            # Use enhanced CDC with record-level deduplication
            cdc_config = CDCConfig(
                checkpoint_dir="src/storage/lakehouse/cdc/silver",
                enable_file_tracking=True,
                enable_record_dedup=True,
                enable_watermarks=True,
            )
            self._cdc_manager = CDCManager(cdc_config)
            self.cdc = None  # Disabled legacy CDC
        else:
            # Use legacy CDC (file-level only)
            self.cdc = ChangeDataCapture(self.config.checkpoint_file)
            self._cdc_manager = None

        # Processing statistics
        self._stats = {
            "files_processed": 0,
            "records_transformed": 0,
            "duplicates_skipped": 0,
        }

        # Ensure output directory exists
        os.makedirs(self.config.silver_path, exist_ok=True)

    def list_bronze_files(self) -> List[str]:
        """List all files in Bronze layer."""
        files = []
        for root, dirs, filenames in os.walk(self.config.bronze_path):
            for filename in filenames:
                if filename.endswith((".parquet", ".json")):
                    files.append(os.path.join(root, filename))
        return sorted(files)

    def list_new_files(self) -> List[str]:
        """List Bronze files not yet processed (CDC)."""
        if self._use_enhanced_cdc:
            # Use enhanced CDC file tracker
            return self._cdc_manager.get_pending_files(
                self.config.bronze_path, "*.parquet"
            ) + self._cdc_manager.get_pending_files(
                self.config.bronze_path, "*.json"
            )
        else:
            # Use legacy CDC
            return [f for f in self.list_bronze_files() if not self.cdc.is_processed(f)]

    def read_bronze_file(self, file_path: str) -> List[Dict]:
        """Read a Bronze layer file."""
        if file_path.endswith(".parquet"):
            if pq is None:
                raise ImportError("pyarrow required for Parquet files")

            table = pq.read_table(file_path)
            records = []

            for i in range(table.num_rows):
                row = {col: table.column(col)[i].as_py() for col in table.column_names}
                if "raw_payload" in row:
                    records.append(json.loads(row["raw_payload"]))
                else:
                    records.append(row)

            return records

        elif file_path.endswith(".json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                return data.get("messages", [data])

        raise ValueError(f"Unsupported format: {file_path}")

    def transform_file(self, file_path: str, deduplicate: bool = True) -> List[Dict]:
        """
        Transform a single Bronze file to Silver format.
        
        Args:
            file_path: Path to Bronze file
            deduplicate: If True, skip duplicate records (requires enhanced CDC)
            
        Returns:
            List of transformed records
        """
        raw_records = self.read_bronze_file(file_path)

        transformed = []
        duplicates = 0
        
        for record in raw_records:
            try:
                # Check for duplicate (enhanced CDC only)
                if deduplicate and self._use_enhanced_cdc:
                    if self._cdc_manager.is_duplicate(record):
                        duplicates += 1
                        continue
                
                flat = self.flattener.flatten_delivery(record)
                transformed.append(flat)
                
                # Mark record as seen (enhanced CDC only)
                if self._use_enhanced_cdc:
                    self._cdc_manager.mark_seen(record)
                    
            except Exception as e:
                print(f"[Silver] Error transforming record: {e}")
                continue
        
        self._stats["duplicates_skipped"] += duplicates
        if duplicates > 0:
            print(f"[Silver] Skipped {duplicates} duplicate records")

        return transformed

    def write_silver_output(
        self,
        records: List[Dict],
        output_name: str,
    ) -> str:
        """Write transformed records to Silver layer."""
        if not records:
            return ""

        timestamp = datetime.utcnow()
        partition_dir = os.path.join(
            self.config.silver_path,
            "deliveries",
            timestamp.strftime("%Y/%m/%d"),
        )
        os.makedirs(partition_dir, exist_ok=True)

        file_id = hashlib.md5(
            f"{timestamp.isoformat()}_{output_name}".encode()
        ).hexdigest()[:8]

        if self.config.output_format == "parquet" and pa is not None:
            filename = (
                f"deliveries_{timestamp.strftime('%Y%m%d_%H%M%S')}_{file_id}.parquet"
            )
            file_path = os.path.join(partition_dir, filename)

            table = pa.Table.from_pylist(records)
            pq.write_table(
                table,
                file_path,
                compression=(
                    self.config.compression
                    if self.config.compression != "none"
                    else None
                ),
            )
        else:
            filename = f"deliveries_{timestamp.strftime('%Y%m%d_%H%M%S')}_{file_id}.csv"
            file_path = os.path.join(partition_dir, filename)

            if pd is not None:
                df = pd.DataFrame(records)
                df.to_csv(file_path, index=False)
            else:
                # Fallback to JSON
                filename = filename.replace(".csv", ".json")
                file_path = os.path.join(partition_dir, filename)
                with open(file_path, "w") as f:
                    json.dump(records, f, indent=2)

        return file_path

    def run_incremental(self) -> Tuple[int, int]:
        """
        Run incremental ELT (process only new Bronze files).

        Uses CDC to track processed files and avoid reprocessing.
        With enhanced CDC, also deduplicates records.

        Returns:
            Tuple of (files_processed, records_transformed)
        """
        new_files = self.list_new_files()

        if not new_files:
            print("[Silver] No new files to process")
            return 0, 0

        print(f"[Silver] Processing {len(new_files)} new Bronze files...")

        total_records = 0
        all_transformed = []

        for file_path in new_files:
            try:
                transformed = self.transform_file(file_path, deduplicate=True)
                all_transformed.extend(transformed)
                total_records += len(transformed)

                # Mark file as processed
                if self._use_enhanced_cdc:
                    self._cdc_manager.mark_file_processed(file_path)
                else:
                    self.cdc.mark_processed(file_path)
                    
                print(f"[Silver] Processed: {file_path} ({len(transformed)} records)")

            except Exception as e:
                print(f"[Silver] Error processing {file_path}: {e}")
                continue

        # Update stats
        self._stats["files_processed"] += len(new_files)
        self._stats["records_transformed"] += total_records

        # Write output
        if all_transformed:
            output_path = self.write_silver_output(all_transformed, "incremental")
            print(f"[Silver] Output written to: {output_path}")
            
            # Update watermark (enhanced CDC only)
            if self._use_enhanced_cdc:
                self._cdc_manager.update_watermark("silver_output", output_path)

        # Commit checkpoint
        if self._use_enhanced_cdc:
            self._cdc_manager.commit()
        else:
            self.cdc.commit()

        return len(new_files), total_records

    def run_full(self) -> Tuple[int, int]:
        """
        Run full ELT (reprocess all Bronze files).

        Resets CDC state and reprocesses everything.

        Returns:
            Tuple of (files_processed, records_transformed)
        """
        # Reset CDC checkpoint
        if self._use_enhanced_cdc:
            self._cdc_manager.reset()
        else:
            self.cdc.reset()

        return self.run_incremental()

    def get_statistics(self) -> Dict:
        """Get Silver layer statistics including CDC metrics."""
        silver_files = []
        for root, dirs, filenames in os.walk(self.config.silver_path):
            for filename in filenames:
                if filename.endswith((".parquet", ".csv", ".json")):
                    silver_files.append(os.path.join(root, filename))

        total_size = sum(os.path.getsize(f) for f in silver_files)

        stats = {
            "total_files": len(silver_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "bronze_files_total": len(self.list_bronze_files()),
            "bronze_files_pending": len(self.list_new_files()),
            # Session stats
            "session_files_processed": self._stats["files_processed"],
            "session_records_transformed": self._stats["records_transformed"],
            "session_duplicates_skipped": self._stats["duplicates_skipped"],
        }
        
        # Add CDC-specific stats
        if self._use_enhanced_cdc:
            cdc_stats = self._cdc_manager.get_stats()
            stats["cdc_mode"] = "enhanced"
            stats["cdc_files_tracked"] = cdc_stats.get("files_tracked", 0)
            stats["cdc_records_deduped"] = cdc_stats.get("records_seen", 0)
        else:
            stats["cdc_mode"] = "legacy"
            
        return stats

    def transform_record(self, raw_record: Dict, deduplicate: bool = True) -> Optional[Dict]:
        """
        Transform a single raw record to Silver format (for orchestrator integration).
        
        This method is designed for real-time/streaming processing where records
        are processed individually rather than in batch files.
        
        Args:
            raw_record: Raw message from Kafka/Bronze layer
            deduplicate: If True, check for and skip duplicate records (enhanced CDC)
            
        Returns:
            Flattened, cleansed Silver record, or None if transformation fails or duplicate
        """
        try:
            # Check for duplicate (enhanced CDC only)
            if deduplicate and self._use_enhanced_cdc:
                if self._cdc_manager.is_duplicate(raw_record):
                    self._stats["duplicates_skipped"] += 1
                    return None
            
            flat = self.flattener.flatten_delivery(raw_record)
            
            # Mark as seen (enhanced CDC only)
            if self._use_enhanced_cdc:
                self._cdc_manager.mark_seen(raw_record)
                
            return flat
            
        except Exception as e:
            print(f"[Silver] Error transforming record: {e}")
            return None


def main():
    """CLI entry point for Silver layer operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Silver Layer ELT Transformer")
    parser.add_argument(
        "--mode",
        "-m",
        choices=["incremental", "full", "stats", "reset"],
        default="incremental",
        help="Operation mode",
    )
    parser.add_argument(
        "--bronze-path",
        default="src/storage/lakehouse/bronze",
        help="Bronze layer path",
    )
    parser.add_argument(
        "--silver-path",
        default="src/storage/lakehouse/silver",
        help="Silver layer path",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["parquet", "csv"],
        default="parquet",
        help="Output format",
    )
    parser.add_argument(
        "--enhanced-cdc",
        action="store_true",
        help="Use enhanced CDC with record-level deduplication",
    )

    args = parser.parse_args()

    config = SilverConfig(
        bronze_path=args.bronze_path,
        silver_path=args.silver_path,
        output_format=args.format,
    )

    transformer = SilverTransformer(config, use_enhanced_cdc=args.enhanced_cdc)
    
    print(f"[Silver] CDC Mode: {'enhanced' if transformer._use_enhanced_cdc else 'legacy'}")

    if args.mode == "incremental":
        files, records = transformer.run_incremental()
        print(f"\n[Silver] Complete: {files} files, {records} records")

    elif args.mode == "full":
        files, records = transformer.run_full()
        print(f"\n[Silver] Full refresh complete: {files} files, {records} records")

    elif args.mode == "stats":
        stats = transformer.get_statistics()
        print("Silver Layer Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    elif args.mode == "reset":
        if transformer._use_enhanced_cdc:
            transformer._cdc_manager.reset()
        else:
            transformer.cdc.reset()
        print("[Silver] CDC checkpoint reset - next run will reprocess all files")


if __name__ == "__main__":
    main()

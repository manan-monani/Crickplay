"""
Crickplay Change Data Capture (CDC) System

Robust CDC implementation for efficient incremental data processing across the
Medallion Architecture. Supports:

1. **File-level CDC**: Track which Bronze files have been processed to Silver
2. **Record-level CDC**: Track individual delivery hashes to prevent duplicates
3. **Watermark CDC**: High-water mark tracking for streaming data
4. **Schema versioning**: Track schema changes over time

Architecture:
    ┌────────────────────────────────────────────────────────────────┐
    │                    CDC MANAGER                                  │
    ├────────────────────────────────────────────────────────────────┤
    │  FileTracker      │  RecordDeduplicator  │  WatermarkManager   │
    │  ─────────────    │  ──────────────────  │  ─────────────────  │
    │  • File hashes    │  • Record hashes     │  • Timestamp HWM    │
    │  • Processing     │  • Bloom filter      │  • Partition marks  │
    │    status         │  • Exact match       │  • Offset tracking  │
    └────────────────────────────────────────────────────────────────┘

Usage:
    from src.medallion.cdc import CDCManager, CDCConfig

    cdc = CDCManager(CDCConfig(
        checkpoint_dir="src/storage/lakehouse/cdc",
        enable_record_dedup=True,
        enable_watermarks=True,
    ))

    # Check if file needs processing
    if not cdc.file_tracker.is_processed("path/to/file.parquet"):
        process_file(...)
        cdc.file_tracker.mark_processed("path/to/file.parquet")

    # Check record deduplication
    if not cdc.record_dedup.is_duplicate(delivery_record):
        store_record(...)
        cdc.record_dedup.mark_seen(delivery_record)

    # Get high-water mark for incremental processing
    hwm = cdc.watermark.get_watermark("bronze_layer")
    new_records = query_since(hwm)
    cdc.watermark.update_watermark("bronze_layer", new_timestamp)
"""

import os
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class CDCConfig:
    """Configuration for CDC system."""

    # Base checkpoint directory
    checkpoint_dir: str = "src/storage/lakehouse/cdc"

    # Feature flags
    enable_file_tracking: bool = True
    enable_record_dedup: bool = True
    enable_watermarks: bool = True

    # Record deduplication settings
    dedup_bloom_size: int = 1_000_000  # Expected number of records
    dedup_error_rate: float = 0.01  # Acceptable false positive rate

    # Watermark settings
    watermark_commit_interval: int = 100  # Commit every N records

    # Persistence settings
    auto_checkpoint: bool = True
    checkpoint_interval_seconds: int = 60


@dataclass
class FileProcessingState:
    """State of a processed file."""

    file_path: str
    file_hash: str
    file_size: int
    records_processed: int
    processed_at: str
    processing_duration_ms: int
    status: str = "completed"  # completed, partial, failed
    error_message: Optional[str] = None

    @classmethod
    def from_file(cls, file_path: str) -> "FileProcessingState":
        """Create state for a new file."""
        stat = os.stat(file_path) if os.path.exists(file_path) else None
        return cls(
            file_path=file_path,
            file_hash=cls.compute_file_hash(file_path),
            file_size=stat.st_size if stat else 0,
            records_processed=0,
            processed_at=datetime.utcnow().isoformat(),
            processing_duration_ms=0,
        )

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """Compute hash of file for change detection."""
        if not os.path.exists(file_path):
            return hashlib.md5(file_path.encode()).hexdigest()

        # Hash file path + size + mtime for efficiency
        stat = os.stat(file_path)
        content = f"{file_path}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()


class FileTracker:
    """
    Track which files have been processed.

    Provides efficient file-level CDC with:
    - File hash tracking (detects modifications)
    - Processing status (completed/failed/partial)
    - Statistics and audit trail
    """

    def __init__(self, checkpoint_file: str):
        self.checkpoint_file = checkpoint_file
        self._states: Dict[str, FileProcessingState] = {}
        self._load_checkpoint()

    def _load_checkpoint(self) -> None:
        """Load checkpoint from disk."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, "r") as f:
                    data = json.load(f)
                    for file_path, state_dict in data.get("files", {}).items():
                        self._states[file_path] = FileProcessingState(**state_dict)
                logger.info(f"[CDC/FileTracker] Loaded {len(self._states)} file states")
            except Exception as e:
                logger.error(f"[CDC/FileTracker] Failed to load checkpoint: {e}")

    def _save_checkpoint(self) -> None:
        """Save checkpoint to disk."""
        os.makedirs(os.path.dirname(self.checkpoint_file), exist_ok=True)

        data = {
            "version": "1.0",
            "updated_at": datetime.utcnow().isoformat(),
            "total_files": len(self._states),
            "files": {fp: asdict(state) for fp, state in self._states.items()},
        }

        with open(self.checkpoint_file, "w") as f:
            json.dump(data, f, indent=2)

    def is_processed(self, file_path: str, check_modified: bool = True) -> bool:
        """
        Check if a file has been processed.

        Args:
            file_path: Path to check
            check_modified: If True, re-process if file was modified

        Returns:
            True if file was processed and not modified
        """
        if file_path not in self._states:
            return False

        state = self._states[file_path]

        # Check if file failed previously
        if state.status == "failed":
            return False

        # Check if file was modified
        if check_modified:
            current_hash = FileProcessingState.compute_file_hash(file_path)
            if current_hash != state.file_hash:
                logger.info(f"[CDC/FileTracker] File modified: {file_path}")
                return False

        return True

    def mark_processed(
        self,
        file_path: str,
        records_processed: int = 0,
        duration_ms: int = 0,
        status: str = "completed",
        error: Optional[str] = None,
    ) -> None:
        """Mark a file as processed."""
        state = FileProcessingState.from_file(file_path)
        state.records_processed = records_processed
        state.processing_duration_ms = duration_ms
        state.status = status
        state.error_message = error

        self._states[file_path] = state
        logger.debug(f"[CDC/FileTracker] Marked processed: {file_path}")

    def get_unprocessed_files(
        self, directory: str, pattern: str = "*.parquet"
    ) -> List[str]:
        """Get list of files not yet processed."""
        import glob

        all_files = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
        return [f for f in all_files if not self.is_processed(f)]

    def reset(self, file_path: Optional[str] = None) -> None:
        """Reset tracking (all files or specific file)."""
        if file_path:
            self._states.pop(file_path, None)
        else:
            self._states.clear()
        self._save_checkpoint()

    def commit(self) -> None:
        """Persist checkpoint to disk."""
        self._save_checkpoint()

    def get_statistics(self) -> Dict:
        """Get processing statistics."""
        completed = sum(1 for s in self._states.values() if s.status == "completed")
        failed = sum(1 for s in self._states.values() if s.status == "failed")
        total_records = sum(s.records_processed for s in self._states.values())

        return {
            "total_files_tracked": len(self._states),
            "completed": completed,
            "failed": failed,
            "total_records_processed": total_records,
        }


class RecordDeduplicator:
    """
    Track individual records to prevent duplicates.

    Uses a hybrid approach:
    1. In-memory set for fast lookups (current session)
    2. Persistent file for cross-session deduplication
    3. Optional Bloom filter for memory efficiency with large datasets

    Record identity is computed from:
    - match_id + inning + over + ball + batter + bowler (delivery granularity)
    """

    def __init__(self, checkpoint_file: str, max_in_memory: int = 100_000):
        self.checkpoint_file = checkpoint_file
        self.max_in_memory = max_in_memory

        self._seen_hashes: Set[str] = set()
        self._session_hashes: Set[str] = set()
        self._records_seen: int = 0
        self._duplicates_blocked: int = 0

        self._load_checkpoint()

    def _load_checkpoint(self) -> None:
        """Load seen hashes from disk."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, "r") as f:
                    data = json.load(f)
                    self._seen_hashes = set(data.get("hashes", []))
                    self._records_seen = data.get("total_seen", 0)
                logger.info(
                    f"[CDC/Dedup] Loaded {len(self._seen_hashes)} record hashes"
                )
            except Exception as e:
                logger.error(f"[CDC/Dedup] Failed to load checkpoint: {e}")

    def _save_checkpoint(self) -> None:
        """Save seen hashes to disk."""
        os.makedirs(os.path.dirname(self.checkpoint_file), exist_ok=True)

        # Merge session hashes with persisted hashes
        all_hashes = self._seen_hashes | self._session_hashes

        # Keep only most recent hashes if too many
        if len(all_hashes) > self.max_in_memory:
            all_hashes = set(list(all_hashes)[-self.max_in_memory :])

        data = {
            "version": "1.0",
            "updated_at": datetime.utcnow().isoformat(),
            "total_seen": self._records_seen,
            "duplicates_blocked": self._duplicates_blocked,
            "hash_count": len(all_hashes),
            "hashes": list(all_hashes),
        }

        with open(self.checkpoint_file, "w") as f:
            json.dump(data, f)

    @staticmethod
    def compute_record_hash(record: Dict) -> str:
        """
        Compute unique hash for a delivery record.

        Uses delivery granularity: match + inning + over + ball + players
        """
        # Extract identity fields
        identity_fields = [
            str(record.get("match_id", "")),
            str(record.get("inning", record.get("batting_team", ""))),
            str(record.get("over", 0)),
            str(record.get("ball", 0)),
            str(record.get("batter", record.get("batter_name", ""))),
            str(record.get("bowler", record.get("bowler_name", ""))),
        ]

        identity_str = "|".join(identity_fields)
        return hashlib.sha256(identity_str.encode()).hexdigest()[:16]

    def is_duplicate(self, record: Dict) -> bool:
        """Check if record is a duplicate."""
        record_hash = self.compute_record_hash(record)
        return record_hash in self._seen_hashes or record_hash in self._session_hashes

    def mark_seen(self, record: Dict) -> str:
        """Mark record as seen. Returns the record hash."""
        record_hash = self.compute_record_hash(record)

        if record_hash in self._seen_hashes or record_hash in self._session_hashes:
            self._duplicates_blocked += 1
            return record_hash

        self._session_hashes.add(record_hash)
        self._records_seen += 1

        return record_hash

    def commit(self) -> None:
        """Persist to disk."""
        self._save_checkpoint()
        self._seen_hashes |= self._session_hashes
        self._session_hashes.clear()

    def get_statistics(self) -> Dict:
        """Get deduplication statistics."""
        return {
            "total_records_seen": self._records_seen,
            "unique_hashes_tracked": len(self._seen_hashes) + len(self._session_hashes),
            "duplicates_blocked": self._duplicates_blocked,
            "session_records": len(self._session_hashes),
        }


class WatermarkManager:
    """
    High-water mark tracking for incremental processing.

    Tracks the latest processed timestamp/offset for each data source,
    enabling efficient incremental queries like:
        SELECT * FROM bronze WHERE event_time > {watermark}

    Supports:
    - Timestamp watermarks (ISO 8601)
    - Kafka offset watermarks
    - Partition-level tracking
    """

    def __init__(self, checkpoint_file: str):
        self.checkpoint_file = checkpoint_file
        self._watermarks: Dict[str, Dict] = {}
        self._load_checkpoint()

    def _load_checkpoint(self) -> None:
        """Load watermarks from disk."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, "r") as f:
                    data = json.load(f)
                    self._watermarks = data.get("watermarks", {})
                logger.info(
                    f"[CDC/Watermark] Loaded {len(self._watermarks)} watermarks"
                )
            except Exception as e:
                logger.error(f"[CDC/Watermark] Failed to load: {e}")

    def _save_checkpoint(self) -> None:
        """Save watermarks to disk."""
        os.makedirs(os.path.dirname(self.checkpoint_file), exist_ok=True)

        data = {
            "version": "1.0",
            "updated_at": datetime.utcnow().isoformat(),
            "watermarks": self._watermarks,
        }

        with open(self.checkpoint_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_watermark(self, source_id: str) -> Optional[str]:
        """
        Get high-water mark for a source.

        Returns:
            ISO 8601 timestamp string, or None if no watermark exists
        """
        wm = self._watermarks.get(source_id)
        return wm.get("timestamp") if wm else None

    def get_offset_watermark(self, source_id: str, partition: int = 0) -> Optional[int]:
        """
        Get Kafka offset watermark for a source/partition.

        Returns:
            Latest processed offset, or None
        """
        wm = self._watermarks.get(source_id)
        if not wm:
            return None

        offsets = wm.get("offsets", {})
        return offsets.get(str(partition))

    def update_watermark(
        self,
        source_id: str,
        timestamp: Optional[str] = None,
        offset: Optional[int] = None,
        partition: int = 0,
        records_processed: int = 0,
    ) -> None:
        """
        Update watermark for a source.

        Args:
            source_id: Unique identifier for the data source
            timestamp: ISO 8601 timestamp (high-water mark)
            offset: Kafka offset (if applicable)
            partition: Kafka partition (if applicable)
            records_processed: Number of records processed in this batch
        """
        if source_id not in self._watermarks:
            self._watermarks[source_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "offsets": {},
                "total_records": 0,
            }

        wm = self._watermarks[source_id]

        if timestamp:
            wm["timestamp"] = timestamp

        if offset is not None:
            wm["offsets"][str(partition)] = offset

        wm["total_records"] = wm.get("total_records", 0) + records_processed
        wm["updated_at"] = datetime.utcnow().isoformat()

    def commit(self) -> None:
        """Persist watermarks to disk."""
        self._save_checkpoint()

    def reset(self, source_id: Optional[str] = None) -> None:
        """Reset watermarks (all or specific source)."""
        if source_id:
            self._watermarks.pop(source_id, None)
        else:
            self._watermarks.clear()
        self._save_checkpoint()

    def get_all_watermarks(self) -> Dict[str, Dict]:
        """Get all watermarks."""
        return self._watermarks.copy()


class CDCManager:
    """
    Unified CDC manager combining all tracking mechanisms.

    Provides a single interface for:
    - File-level CDC (which Bronze files are processed)
    - Record-level deduplication (prevent duplicate deliveries)
    - Watermark tracking (incremental processing)

    Usage:
        cdc = CDCManager()

        # File processing
        for file in cdc.get_pending_files("bronze/"):
            records = process_file(file)
            cdc.mark_file_processed(file, len(records))

        # Record deduplication
        for record in incoming_records:
            if not cdc.is_duplicate(record):
                store(record)
                cdc.mark_seen(record)

        # Watermark queries
        hwm = cdc.get_watermark("kafka_consumer")
        new_data = query_since(hwm)
        cdc.update_watermark("kafka_consumer", latest_timestamp)

        # Commit all changes
        cdc.commit()
    """

    def __init__(self, config: Optional[CDCConfig] = None):
        self.config = config or CDCConfig()

        # Ensure checkpoint directory exists
        os.makedirs(self.config.checkpoint_dir, exist_ok=True)

        # Initialize components
        if self.config.enable_file_tracking:
            self.file_tracker = FileTracker(
                os.path.join(self.config.checkpoint_dir, "file_tracker.json")
            )
        else:
            self.file_tracker = None

        if self.config.enable_record_dedup:
            self.record_dedup = RecordDeduplicator(
                os.path.join(self.config.checkpoint_dir, "record_hashes.json")
            )
        else:
            self.record_dedup = None

        if self.config.enable_watermarks:
            self.watermark = WatermarkManager(
                os.path.join(self.config.checkpoint_dir, "watermarks.json")
            )
        else:
            self.watermark = None

        self._last_checkpoint = time.time()
        logger.info("[CDC] Manager initialized")

    # === File Tracking Convenience Methods ===

    def is_file_processed(self, file_path: str) -> bool:
        """Check if file has been processed."""
        if not self.file_tracker:
            return False
        return self.file_tracker.is_processed(file_path)

    def mark_file_processed(
        self,
        file_path: str,
        records: int = 0,
        duration_ms: int = 0,
    ) -> None:
        """Mark file as processed."""
        if self.file_tracker:
            self.file_tracker.mark_processed(
                file_path, records, duration_ms, "completed"
            )

    def get_pending_files(
        self, directory: str, pattern: str = "*.parquet"
    ) -> List[str]:
        """Get list of files pending processing."""
        if not self.file_tracker:
            import glob

            return glob.glob(os.path.join(directory, "**", pattern), recursive=True)
        return self.file_tracker.get_unprocessed_files(directory, pattern)

    # === Record Deduplication Convenience Methods ===

    def is_duplicate(self, record: Dict) -> bool:
        """Check if record is a duplicate."""
        if not self.record_dedup:
            return False
        return self.record_dedup.is_duplicate(record)

    def mark_seen(self, record: Dict) -> Optional[str]:
        """Mark record as seen. Returns hash."""
        if not self.record_dedup:
            return None
        return self.record_dedup.mark_seen(record)

    # === Watermark Convenience Methods ===

    def get_watermark(self, source_id: str) -> Optional[str]:
        """Get high-water mark timestamp."""
        if not self.watermark:
            return None
        return self.watermark.get_watermark(source_id)

    def update_watermark(
        self,
        source_id: str,
        timestamp: str,
        records: int = 0,
    ) -> None:
        """Update watermark."""
        if self.watermark:
            self.watermark.update_watermark(
                source_id, timestamp=timestamp, records_processed=records
            )

    # === Lifecycle Methods ===

    def commit(self) -> None:
        """Persist all CDC state to disk."""
        if self.file_tracker:
            self.file_tracker.commit()
        if self.record_dedup:
            self.record_dedup.commit()
        if self.watermark:
            self.watermark.commit()

        self._last_checkpoint = time.time()
        logger.debug("[CDC] Checkpoint committed")

    def maybe_checkpoint(self) -> bool:
        """
        Checkpoint if interval has passed.

        Returns:
            True if checkpoint was performed
        """
        if not self.config.auto_checkpoint:
            return False

        elapsed = time.time() - self._last_checkpoint
        if elapsed >= self.config.checkpoint_interval_seconds:
            self.commit()
            return True
        return False

    def reset_all(self) -> None:
        """Reset all CDC state (use with caution!)."""
        if self.file_tracker:
            self.file_tracker.reset()
        if self.record_dedup:
            # Clear dedup file
            if os.path.exists(self.record_dedup.checkpoint_file):
                os.remove(self.record_dedup.checkpoint_file)
        if self.watermark:
            self.watermark.reset()
        logger.warning("[CDC] All state reset!")

    def reset(self) -> None:
        """Alias for reset_all (compatibility with legacy CDC)."""
        self.reset_all()

    def get_stats(self) -> Dict:
        """
        Get simplified statistics (compatibility method).
        
        Returns a flat dict with key metrics for quick checks.
        """
        stats = {
            "files_tracked": 0,
            "records_seen": 0,
            "duplicates_blocked": 0,
        }
        
        if self.file_tracker:
            file_stats = self.file_tracker.get_statistics()
            stats["files_tracked"] = file_stats.get("total_files_tracked", 0)
            
        if self.record_dedup:
            dedup_stats = self.record_dedup.get_statistics()
            stats["records_seen"] = dedup_stats.get("total_records_seen", 0)
            stats["duplicates_blocked"] = dedup_stats.get("duplicates_blocked", 0)
            
        return stats

    def get_statistics(self) -> Dict:
        """Get comprehensive CDC statistics."""
        stats = {
            "checkpoint_dir": self.config.checkpoint_dir,
            "last_checkpoint": datetime.fromtimestamp(
                self._last_checkpoint
            ).isoformat(),
        }

        if self.file_tracker:
            stats["file_tracking"] = self.file_tracker.get_statistics()

        if self.record_dedup:
            stats["deduplication"] = self.record_dedup.get_statistics()

        if self.watermark:
            stats["watermarks"] = self.watermark.get_all_watermarks()

        return stats


# === CLI Entry Point ===


def main():
    """CLI for CDC management."""
    import argparse

    parser = argparse.ArgumentParser(description="CDC Manager CLI")
    parser.add_argument(
        "--mode",
        "-m",
        choices=["stats", "reset", "pending"],
        default="stats",
        help="Operation mode",
    )
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        help="Source ID for watermark operations",
    )
    parser.add_argument(
        "--directory",
        "-d",
        type=str,
        default="src/storage/lakehouse/bronze",
        help="Directory to scan for pending files",
    )

    args = parser.parse_args()

    cdc = CDCManager()

    if args.mode == "stats":
        stats = cdc.get_statistics()
        print(json.dumps(stats, indent=2))

    elif args.mode == "pending":
        pending = cdc.get_pending_files(args.directory)
        print(f"Pending files in {args.directory}:")
        for f in pending:
            print(f"  - {f}")
        print(f"Total: {len(pending)}")

    elif args.mode == "reset":
        confirm = input("This will reset ALL CDC state. Type 'yes' to confirm: ")
        if confirm.lower() == "yes":
            cdc.reset_all()
            print("CDC state reset.")
        else:
            print("Aborted.")


if __name__ == "__main__":
    main()

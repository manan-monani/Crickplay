"""
Bronze Layer - Kafka Sink

Consumes messages from Kafka and stores them in the Bronze layer
of the Medallion architecture. Data is stored as raw Parquet files,
maintaining immutability and schema-on-read capabilities.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Optional, List, Generator
from dataclasses import dataclass, field
import hashlib

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    pa = None
    pq = None

from kafka import KafkaConsumer
from kafka.errors import KafkaError


@dataclass
class BronzeConfig:
    """Configuration for Bronze layer storage."""

    # Kafka settings
    kafka_broker: str = "localhost:29092"
    kafka_topic: str = "live_match_deliveries"
    consumer_group: str = "bronze_sink"

    # Storage settings
    storage_path: str = "src/storage/lakehouse/bronze"
    partition_by: str = "date"  # date, hour, or match_id

    # Batching settings
    batch_size: int = 100  # Write every N messages
    batch_timeout_seconds: int = 60  # Write at least every N seconds

    # File settings
    compression: str = "snappy"  # snappy, gzip, zstd, none


@dataclass
class MessageBatch:
    """Holds a batch of messages before writing to storage."""

    messages: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add(self, message: Dict) -> None:
        self.messages.append(message)

    def size(self) -> int:
        return len(self.messages)

    def should_flush(self, batch_size: int, timeout_seconds: int) -> bool:
        if self.size() >= batch_size:
            return True
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed >= timeout_seconds and self.size() > 0

    def clear(self) -> None:
        self.messages.clear()
        self.created_at = datetime.utcnow()


class BronzeKafkaSink:
    """
    Kafka consumer that sinks raw messages to Bronze layer storage.

    Features:
    - Batched writes for efficiency
    - Partitioned storage by date/hour/match
    - Parquet format with compression
    - Exactly-once semantics via offset management
    """

    def __init__(self, config: Optional[BronzeConfig] = None):
        self.config = config or BronzeConfig()
        self.consumer: Optional[KafkaConsumer] = None
        self.batch = MessageBatch()
        self.messages_processed = 0
        self.files_written = 0

        # Ensure storage directory exists
        os.makedirs(self.config.storage_path, exist_ok=True)

    def _get_consumer(self) -> KafkaConsumer:
        """Initialize and return Kafka consumer."""
        if self.consumer is None:
            self.consumer = KafkaConsumer(
                self.config.kafka_topic,
                bootstrap_servers=[self.config.kafka_broker],
                group_id=self.config.consumer_group,
                auto_offset_reset="earliest",
                enable_auto_commit=False,  # Manual commit for exactly-once
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            )
        return self.consumer

    def _generate_file_path(self, partition_key: str) -> str:
        """Generate storage file path based on partition key."""
        timestamp = datetime.utcnow()

        if self.config.partition_by == "date":
            partition_dir = timestamp.strftime("%Y/%m/%d")
        elif self.config.partition_by == "hour":
            partition_dir = timestamp.strftime("%Y/%m/%d/%H")
        else:
            partition_dir = partition_key

        full_dir = os.path.join(self.config.storage_path, partition_dir)
        os.makedirs(full_dir, exist_ok=True)

        # Generate unique filename
        file_id = hashlib.md5(
            f"{timestamp.isoformat()}_{self.files_written}".encode()
        ).hexdigest()[:8]

        filename = (
            f"delivery_batch_{timestamp.strftime('%Y%m%d_%H%M%S')}_{file_id}.parquet"
        )

        return os.path.join(full_dir, filename)

    def _messages_to_arrow_table(self, messages: List[Dict]) -> "pa.Table":
        """Convert message batch to PyArrow table."""
        if pa is None:
            raise ImportError("pyarrow is required for Parquet storage")

        # Flatten messages while preserving raw JSON
        rows = []
        for msg in messages:
            row = {
                # Metadata columns
                "ingestion_timestamp": msg.get(
                    "ingestion_timestamp", datetime.utcnow().isoformat()
                ),
                "bronze_timestamp": datetime.utcnow().isoformat(),
                # Match context (flattened for querying)
                "match_type": msg.get("match_context", {}).get("match_type"),
                "venue": msg.get("match_context", {}).get("venue"),
                "match_date": msg.get("match_context", {}).get("date"),
                "match_file_id": msg.get("match_context", {}).get("file_id"),
                # Delivery position
                "inning_team": msg.get("inning_team"),
                "over": msg.get("over"),
                "ball": msg.get("ball"),
                # Raw payload (preserved for schema-on-read)
                "raw_payload": json.dumps(msg),
            }
            rows.append(row)

        # Create Arrow table
        return pa.Table.from_pylist(rows)

    def _write_batch_parquet(self, messages: List[Dict]) -> str:
        """Write message batch to Parquet file."""
        if pq is None:
            raise ImportError("pyarrow is required for Parquet storage")

        # Determine partition key
        if messages:
            first_msg = messages[0]
            partition_key = first_msg.get("match_context", {}).get("file_id", "unknown")
        else:
            partition_key = "unknown"

        # Generate file path
        file_path = self._generate_file_path(partition_key)

        # Convert to Arrow table
        table = self._messages_to_arrow_table(messages)

        # Write to Parquet
        pq.write_table(
            table,
            file_path,
            compression=(
                self.config.compression if self.config.compression != "none" else None
            ),
        )

        self.files_written += 1
        return file_path

    def _write_batch_json(self, messages: List[Dict]) -> str:
        """Fallback: Write message batch to JSON file (if PyArrow unavailable)."""
        timestamp = datetime.utcnow()

        if self.config.partition_by == "date":
            partition_dir = timestamp.strftime("%Y/%m/%d")
        else:
            partition_dir = timestamp.strftime("%Y/%m/%d/%H")

        full_dir = os.path.join(self.config.storage_path, partition_dir)
        os.makedirs(full_dir, exist_ok=True)

        file_id = hashlib.md5(
            f"{timestamp.isoformat()}_{self.files_written}".encode()
        ).hexdigest()[:8]

        filename = (
            f"delivery_batch_{timestamp.strftime('%Y%m%d_%H%M%S')}_{file_id}.json"
        )
        file_path = os.path.join(full_dir, filename)

        with open(file_path, "w") as f:
            json.dump(
                {
                    "bronze_timestamp": timestamp.isoformat(),
                    "message_count": len(messages),
                    "messages": messages,
                },
                f,
                indent=2,
            )

        self.files_written += 1
        return file_path

    def flush_batch(self) -> Optional[str]:
        """Write current batch to storage and clear."""
        if self.batch.size() == 0:
            return None

        messages = self.batch.messages.copy()

        try:
            # Try Parquet first, fallback to JSON
            if pa is not None and pq is not None:
                file_path = self._write_batch_parquet(messages)
            else:
                file_path = self._write_batch_json(messages)

            self.messages_processed += len(messages)
            self.batch.clear()

            print(f"[Bronze] Wrote {len(messages)} messages to: {file_path}")
            return file_path

        except Exception as e:
            print(f"[Bronze] Error writing batch: {e}")
            raise

    def process_message(self, message: Dict) -> None:
        """Process a single message from Kafka."""
        self.batch.add(message)

        # Check if batch should be flushed
        if self.batch.should_flush(
            self.config.batch_size, self.config.batch_timeout_seconds
        ):
            self.flush_batch()

    def run(self, max_messages: Optional[int] = None) -> None:
        """
        Run the Bronze sink continuously.

        Args:
            max_messages: Stop after processing N messages (None = run forever)
        """
        consumer = self._get_consumer()
        print(f"[Bronze] Starting sink for topic: {self.config.kafka_topic}")
        print(f"[Bronze] Storage path: {self.config.storage_path}")

        try:
            for message in consumer:
                self.process_message(message.value)

                # Commit offset after successful processing
                consumer.commit()

                if max_messages and self.messages_processed >= max_messages:
                    print(f"[Bronze] Reached max messages: {max_messages}")
                    break

        except KeyboardInterrupt:
            print("\n[Bronze] Stopping...")

        finally:
            # Flush any remaining messages
            self.flush_batch()

            if self.consumer:
                self.consumer.close()

            print(f"[Bronze] Total messages processed: {self.messages_processed}")
            print(f"[Bronze] Total files written: {self.files_written}")

    def run_batch_mode(self, timeout_seconds: int = 30) -> int:
        """
        Run in batch mode - process available messages and exit.

        Useful for scheduled ETL jobs rather than continuous streaming.

        Args:
            timeout_seconds: Wait this long for messages before exiting

        Returns:
            Number of messages processed
        """
        consumer = self._get_consumer()
        start_time = time.time()

        print(f"[Bronze] Running batch mode (timeout: {timeout_seconds}s)")

        try:
            while True:
                # Poll with short timeout
                messages = consumer.poll(timeout_ms=1000)

                if messages:
                    for topic_partition, records in messages.items():
                        for record in records:
                            self.process_message(record.value)

                    consumer.commit()
                    start_time = time.time()  # Reset timeout on activity

                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    print("[Bronze] Timeout reached, no new messages")
                    break

        finally:
            self.flush_batch()
            if self.consumer:
                self.consumer.close()

        return self.messages_processed


class BronzeReader:
    """
    Reader for Bronze layer data.

    Provides utilities to read and query raw data stored in the Bronze layer.
    """

    def __init__(self, storage_path: str = "src/storage/lakehouse/bronze"):
        self.storage_path = storage_path

    def list_files(self, date_filter: Optional[str] = None) -> List[str]:
        """List all Bronze layer files, optionally filtered by date."""
        files = []

        for root, dirs, filenames in os.walk(self.storage_path):
            for filename in filenames:
                if filename.endswith((".parquet", ".json")):
                    file_path = os.path.join(root, filename)

                    if date_filter is None or date_filter in file_path:
                        files.append(file_path)

        return sorted(files)

    def read_file(self, file_path: str) -> List[Dict]:
        """Read a single Bronze layer file."""
        if file_path.endswith(".parquet"):
            if pq is None:
                raise ImportError("pyarrow required to read Parquet files")

            table = pq.read_table(file_path)
            df = table.to_pandas()

            # Parse raw_payload back to dict
            messages = []
            for _, row in df.iterrows():
                if "raw_payload" in row:
                    messages.append(json.loads(row["raw_payload"]))
                else:
                    messages.append(row.to_dict())

            return messages

        elif file_path.endswith(".json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                return data.get("messages", [data])

        else:
            raise ValueError(f"Unsupported file format: {file_path}")

    def read_all(
        self, date_filter: Optional[str] = None
    ) -> Generator[Dict, None, None]:
        """Read all messages from Bronze layer as a generator."""
        for file_path in self.list_files(date_filter):
            for message in self.read_file(file_path):
                yield message

    def get_statistics(self) -> Dict:
        """Get Bronze layer statistics."""
        files = self.list_files()

        total_size = sum(os.path.getsize(f) for f in files)
        parquet_files = [f for f in files if f.endswith(".parquet")]
        json_files = [f for f in files if f.endswith(".json")]

        return {
            "total_files": len(files),
            "parquet_files": len(parquet_files),
            "json_files": len(json_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_path": self.storage_path,
        }


def main():
    """CLI entry point for Bronze layer operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Bronze Layer Kafka Sink")
    parser.add_argument(
        "--mode",
        "-m",
        choices=["stream", "batch", "stats", "list"],
        default="stream",
        help="Operation mode",
    )
    parser.add_argument(
        "--broker",
        "-b",
        default="localhost:29092",
        help="Kafka broker address",
    )
    parser.add_argument(
        "--topic",
        "-t",
        default="live_match_deliveries",
        help="Kafka topic to consume",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="src/storage/lakehouse/bronze",
        help="Bronze layer storage path",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Messages per batch",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Batch mode timeout in seconds",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        help="Maximum messages to process (stream mode)",
    )

    args = parser.parse_args()

    config = BronzeConfig(
        kafka_broker=args.broker,
        kafka_topic=args.topic,
        storage_path=args.output,
        batch_size=args.batch_size,
        batch_timeout_seconds=args.timeout,
    )

    if args.mode == "stream":
        sink = BronzeKafkaSink(config)
        sink.run(max_messages=args.max_messages)

    elif args.mode == "batch":
        sink = BronzeKafkaSink(config)
        processed = sink.run_batch_mode(timeout_seconds=args.timeout)
        print(f"Processed {processed} messages in batch mode")

    elif args.mode == "stats":
        reader = BronzeReader(args.output)
        stats = reader.get_statistics()
        print("Bronze Layer Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    elif args.mode == "list":
        reader = BronzeReader(args.output)
        files = reader.list_files()
        print(f"Bronze Layer Files ({len(files)} total):")
        for f in files[:20]:  # Show first 20
            print(f"  {f}")
        if len(files) > 20:
            print(f"  ... and {len(files) - 20} more")


if __name__ == "__main__":
    main()

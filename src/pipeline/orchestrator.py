"""
Crickplay Pipeline Orchestrator

Provides automatic, end-to-end data flow from Kafka through the Medallion architecture:
    Producer → Kafka → Bronze → Silver → Gold

The orchestrator can run in two modes:
1. STREAMING: Continuous processing as data arrives (production)
2. BATCH: Process existing data in chunks (backfill/testing)

Usage:
    # Streaming mode
    python -m src.pipeline.orchestrator --mode streaming

    # Batch mode (process existing Bronze data)
    python -m src.pipeline.orchestrator --mode batch

Architecture:
    ┌──────────┐    ┌─────────┐    ┌────────┐    ┌────────┐    ┌──────┐
    │ Producer │───►│  Kafka  │───►│ Bronze │───►│ Silver │───►│ Gold │
    └──────────┘    └─────────┘    └────────┘    └────────┘    └──────┘
                                        │
                                        ▼
                                  ┌──────────┐
                                  │ FastAPI  │
                                  │   SSE    │
                                  └──────────┘
"""

import os
import sys
import json
import time
import signal
import threading
import logging
from typing import Dict, Optional, List, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
import argparse
from queue import Queue, Empty

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.ports import KAFKA_CONFIG

# Optional imports for Kafka
try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError

    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

# Import medallion layers
from src.medallion.bronze.kafka_sink import BronzeKafkaSink, BronzeConfig
from src.medallion.silver.transformer import SilverTransformer, SilverConfig
from src.medallion.gold.schema import StarSchemaBuilder, GoldConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("orchestrator")


@dataclass
class PipelineConfig:
    """Configuration for the pipeline orchestrator."""

    # Operation mode
    mode: str = "streaming"  # streaming, batch

    # Kafka settings (for streaming mode)
    kafka_broker: str = "localhost:29092"
    kafka_topic: str = "live_match_deliveries"
    consumer_group: str = "pipeline_orchestrator"

    # Storage paths
    bronze_path: str = "src/storage/lakehouse/bronze"
    silver_path: str = "src/storage/lakehouse/silver"
    gold_path: str = "src/storage/lakehouse/gold"

    # Processing settings
    batch_size: int = 100  # Process N records at a time
    poll_timeout_ms: int = 1000  # Kafka poll timeout

    # Enable/disable layers
    enable_bronze: bool = True
    enable_silver: bool = True
    enable_gold: bool = True

    # Callbacks (for dashboard integration)
    on_bronze_write: Optional[Callable] = None
    on_silver_write: Optional[Callable] = None
    on_gold_write: Optional[Callable] = None
    on_error: Optional[Callable] = None


class PipelineMetrics:
    """Thread-safe metrics collection for pipeline monitoring."""

    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        with self._lock:
            self.kafka_messages_received = 0
            self.bronze_records_written = 0
            self.silver_records_written = 0
            self.gold_records_written = 0
            self.errors = 0
            self.start_time = datetime.utcnow()
            self.last_message_time: Optional[datetime] = None

    def increment(self, metric: str, count: int = 1):
        with self._lock:
            current = getattr(self, metric, 0)
            setattr(self, metric, current + count)

    def get_stats(self) -> Dict:
        with self._lock:
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            return {
                "kafka_messages_received": self.kafka_messages_received,
                "bronze_records_written": self.bronze_records_written,
                "silver_records_written": self.silver_records_written,
                "gold_records_written": self.gold_records_written,
                "errors": self.errors,
                "uptime_seconds": elapsed,
                "throughput_per_second": self.kafka_messages_received / max(1, elapsed),
                "last_message_time": (
                    self.last_message_time.isoformat()
                    if self.last_message_time
                    else None
                ),
            }


class PipelineOrchestrator:
    """
    Orchestrates the complete data pipeline from Kafka through Medallion layers.

    Provides automatic, continuous processing where:
    1. Kafka messages are consumed and written to Bronze (raw)
    2. Bronze records are transformed and written to Silver (cleansed)
    3. Silver records are aggregated into Gold (star schema)

    All processing happens in-process with thread-safe components.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.metrics = PipelineMetrics()
        self._running = False
        self._stop_event = threading.Event()

        # Message queue for inter-layer communication
        self._bronze_queue: Queue = Queue(maxsize=1000)
        self._silver_queue: Queue = Queue(maxsize=1000)

        # Initialize components (lazy)
        self._bronze_sink: Optional[BronzeKafkaSink] = None
        self._silver_transformer: Optional[SilverTransformer] = None
        self._gold_builder: Optional[StarSchemaBuilder] = None

        # Worker threads
        self._threads: List[threading.Thread] = []

        logger.info(f"Pipeline Orchestrator initialized in {self.config.mode} mode")

    def _init_bronze(self) -> BronzeKafkaSink:
        """Initialize Bronze layer sink."""
        if self._bronze_sink is None:
            bronze_config = BronzeConfig(
                kafka_broker=self.config.kafka_broker,
                kafka_topic=self.config.kafka_topic,
                consumer_group=self.config.consumer_group,
                storage_path=self.config.bronze_path,
            )
            self._bronze_sink = BronzeKafkaSink(bronze_config)
        return self._bronze_sink

    def _init_silver(self) -> SilverTransformer:
        """Initialize Silver layer transformer with enhanced CDC."""
        if self._silver_transformer is None:
            silver_config = SilverConfig(
                bronze_path=self.config.bronze_path,
                silver_path=self.config.silver_path,
            )
            # Use enhanced CDC for production pipelines
            self._silver_transformer = SilverTransformer(
                config=silver_config,
                use_enhanced_cdc=True,  # Enable record-level deduplication
            )
        return self._silver_transformer

    def _init_gold(self) -> StarSchemaBuilder:
        """Initialize Gold layer builder."""
        if self._gold_builder is None:
            gold_config = GoldConfig(
                silver_path=self.config.silver_path,
                gold_path=self.config.gold_path,
            )
            self._gold_builder = StarSchemaBuilder(gold_config)
        return self._gold_builder

    def _kafka_consumer_worker(self):
        """
        Worker thread: Consumes from Kafka and passes to Bronze layer.
        Implements the streaming ingestion pattern.
        """
        if not KAFKA_AVAILABLE:
            logger.error("Kafka not available. Install kafka-python.")
            return

        logger.info("Starting Kafka consumer worker...")

        consumer = KafkaConsumer(
            self.config.kafka_topic,
            bootstrap_servers=[self.config.kafka_broker],
            group_id=self.config.consumer_group,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
        )

        while not self._stop_event.is_set():
            try:
                # Poll for messages
                messages = consumer.poll(timeout_ms=self.config.poll_timeout_ms)

                for topic_partition, records in messages.items():
                    for record in records:
                        if record.value is None:
                            continue

                        # Update metrics
                        self.metrics.increment("kafka_messages_received")
                        self.metrics.last_message_time = datetime.utcnow()

                        # Add to Bronze queue for processing
                        try:
                            self._bronze_queue.put(record.value, timeout=5)
                        except:
                            logger.warning("Bronze queue full, dropping message")
                            self.metrics.increment("errors")

            except Exception as e:
                logger.error(f"Kafka consumer error: {e}")
                self.metrics.increment("errors")
                time.sleep(1)

        consumer.close()
        logger.info("Kafka consumer worker stopped")

    def _bronze_worker(self):
        """
        Worker thread: Processes Bronze layer writes and passes to Silver.
        """
        logger.info("Starting Bronze layer worker...")
        bronze = self._init_bronze()
        batch = []

        while not self._stop_event.is_set():
            try:
                # Get message with timeout
                try:
                    message = self._bronze_queue.get(timeout=1)
                    batch.append(message)
                except Empty:
                    pass

                # Flush batch when full or timeout
                if len(batch) >= self.config.batch_size or (
                    len(batch) > 0 and self._bronze_queue.empty()
                ):
                    # Write to Bronze (Parquet)
                    for msg in batch:
                        bronze.process_single_message(msg)

                        # Forward to Silver queue
                        if self.config.enable_silver:
                            try:
                                self._silver_queue.put(msg, timeout=1)
                            except:
                                pass

                    self.metrics.increment("bronze_records_written", len(batch))

                    if self.config.on_bronze_write:
                        self.config.on_bronze_write(len(batch))

                    batch.clear()

            except Exception as e:
                logger.error(f"Bronze worker error: {e}")
                self.metrics.increment("errors")

        # Final flush
        if batch:
            for msg in batch:
                bronze.process_single_message(msg)
            self.metrics.increment("bronze_records_written", len(batch))

        logger.info("Bronze layer worker stopped")

    def _silver_worker(self):
        """
        Worker thread: Transforms Silver layer data and passes to Gold.
        """
        logger.info("Starting Silver layer worker...")
        silver = self._init_silver()
        gold = self._init_gold() if self.config.enable_gold else None

        while not self._stop_event.is_set():
            try:
                # Get message with timeout
                try:
                    message = self._silver_queue.get(timeout=1)
                except Empty:
                    continue

                # Transform in Silver layer
                silver_record = silver.transform_record(message)

                if silver_record:
                    self.metrics.increment("silver_records_written")

                    if self.config.on_silver_write:
                        self.config.on_silver_write(silver_record)

                    # Forward to Gold layer
                    if gold:
                        gold.process_silver_record(silver_record)
                        self.metrics.increment("gold_records_written")

                        if self.config.on_gold_write:
                            self.config.on_gold_write(silver_record)

            except Exception as e:
                logger.error(f"Silver worker error: {e}")
                self.metrics.increment("errors")

        logger.info("Silver layer worker stopped")

    def start(self):
        """Start the pipeline orchestrator."""
        if self._running:
            logger.warning("Pipeline already running")
            return

        logger.info("=" * 60)
        logger.info("Starting Crickplay Pipeline Orchestrator")
        logger.info("=" * 60)
        logger.info(f"Mode: {self.config.mode}")
        logger.info(f"Kafka: {self.config.kafka_broker} / {self.config.kafka_topic}")
        logger.info(
            f"Bronze: {self.config.enable_bronze} | Silver: {self.config.enable_silver} | Gold: {self.config.enable_gold}"
        )
        logger.info("=" * 60)

        self._running = True
        self._stop_event.clear()
        self.metrics.reset()

        if self.config.mode == "streaming":
            # Start worker threads
            workers = [
                ("kafka-consumer", self._kafka_consumer_worker),
                ("bronze-layer", self._bronze_worker),
                ("silver-layer", self._silver_worker),
            ]

            for name, worker_fn in workers:
                thread = threading.Thread(target=worker_fn, name=name, daemon=True)
                thread.start()
                self._threads.append(thread)
                logger.info(f"Started worker thread: {name}")

        elif self.config.mode == "batch":
            self._run_batch_mode()

    def _run_batch_mode(self):
        """Process existing Bronze data in batch mode."""
        logger.info("Running in batch mode - processing existing Bronze data")

        silver = self._init_silver()
        gold = self._init_gold() if self.config.enable_gold else None

        # Process all Bronze files
        bronze_path = Path(self.config.bronze_path)

        if not bronze_path.exists():
            logger.warning(f"Bronze path does not exist: {bronze_path}")
            return

        # Find all parquet files
        parquet_files = list(bronze_path.glob("**/*.parquet"))
        logger.info(f"Found {len(parquet_files)} Bronze parquet files")

        try:
            import pyarrow.parquet as pq

            for pq_file in parquet_files:
                logger.info(f"Processing: {pq_file.name}")

                table = pq.read_table(str(pq_file))
                df = table.to_pandas()

                for _, row in df.iterrows():
                    # Convert row to dict
                    record = row.to_dict()

                    # Parse raw_data if present
                    if "raw_data" in record and isinstance(record["raw_data"], str):
                        try:
                            record = json.loads(record["raw_data"])
                        except:
                            pass

                    # Transform through Silver
                    silver_record = silver.transform_record(record)

                    if silver_record:
                        self.metrics.increment("silver_records_written")

                        # Build Gold
                        if gold:
                            gold.process_silver_record(silver_record)
                            self.metrics.increment("gold_records_written")

                self.metrics.increment("bronze_records_written", len(df))

        except ImportError:
            logger.error("pyarrow not installed. Run: pip install pyarrow")
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            self.metrics.increment("errors")

        # Flush Gold layer
        if gold:
            gold.flush()

        logger.info("Batch processing complete")
        logger.info(f"Stats: {json.dumps(self.metrics.get_stats(), indent=2)}")

    def stop(self):
        """Stop the pipeline orchestrator gracefully."""
        if not self._running:
            return

        logger.info("Stopping pipeline orchestrator...")
        self._stop_event.set()

        # Wait for threads to finish
        for thread in self._threads:
            thread.join(timeout=5)

        self._threads.clear()
        self._running = False

        # Flush Gold layer
        if self._gold_builder:
            self._gold_builder.flush()

        logger.info("Pipeline stopped")
        logger.info(f"Final stats: {json.dumps(self.metrics.get_stats(), indent=2)}")

    def get_status(self) -> Dict:
        """Get current pipeline status."""
        return {
            "running": self._running,
            "mode": self.config.mode,
            "metrics": self.metrics.get_stats(),
            "queues": {
                "bronze_queue_size": self._bronze_queue.qsize(),
                "silver_queue_size": self._silver_queue.qsize(),
            },
            "threads": [t.name for t in self._threads if t.is_alive()],
        }


def main():
    """CLI entry point for pipeline orchestrator."""
    parser = argparse.ArgumentParser(description="Crickplay Pipeline Orchestrator")
    parser.add_argument(
        "--mode",
        choices=["streaming", "batch"],
        default="streaming",
        help="Pipeline mode: streaming (continuous) or batch (one-time)",
    )
    parser.add_argument(
        "--kafka-broker", default="localhost:29092", help="Kafka broker address"
    )
    parser.add_argument(
        "--kafka-topic", default="live_match_deliveries", help="Kafka topic to consume"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Batch size for processing"
    )
    parser.add_argument(
        "--no-silver", action="store_true", help="Disable Silver layer processing"
    )
    parser.add_argument(
        "--no-gold", action="store_true", help="Disable Gold layer processing"
    )

    args = parser.parse_args()

    config = PipelineConfig(
        mode=args.mode,
        kafka_broker=args.kafka_broker,
        kafka_topic=args.kafka_topic,
        batch_size=args.batch_size,
        enable_silver=not args.no_silver,
        enable_gold=not args.no_gold,
    )

    orchestrator = PipelineOrchestrator(config)

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        orchestrator.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start pipeline
    orchestrator.start()

    # Keep running until stopped
    if config.mode == "streaming":
        try:
            while orchestrator._running:
                time.sleep(10)
                status = orchestrator.get_status()
                logger.info(
                    f"Pipeline status: {json.dumps(status['metrics'], indent=2)}"
                )
        except KeyboardInterrupt:
            orchestrator.stop()


if __name__ == "__main__":
    main()

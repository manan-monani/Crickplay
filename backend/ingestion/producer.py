"""
Kafka Producer for Cricsheet Deliveries
Streams ball-by-ball data to Kafka topics
"""

import json
import time
from pathlib import Path
from typing import Optional

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

from app.config import get_settings
from ingestion.parser import CricsheetParser, DeliveryEvent

settings = get_settings()


class CricketDeliveryProducer:
    """
    Kafka producer for cricket delivery events.

    Streams ball-by-ball data from Cricsheet JSON files to Kafka.
    Supports both batch mode (historical data) and live simulation.
    """

    def __init__(
        self,
        bootstrap_servers: str = None,
        topic: str = None,
    ):
        """
        Initialize the producer.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Target Kafka topic for deliveries
        """
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self.topic = topic or settings.kafka_topic_deliveries

        self.producer_config = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": "crickplay-producer",
            "acks": "all",  # Wait for all replicas
            "retries": 3,
            "retry.backoff.ms": 1000,
        }

        self.producer: Optional[Producer] = None
        self._delivery_count = 0
        self._error_count = 0

    def _delivery_callback(self, err, msg):
        """Callback for message delivery confirmation."""
        if err:
            print(f"Delivery failed: {err}")
            self._error_count += 1
        else:
            self._delivery_count += 1

    def connect(self):
        """Connect to Kafka and create topic if needed."""
        self.producer = Producer(self.producer_config)
        self._ensure_topic_exists()
        print(f"Connected to Kafka at {self.bootstrap_servers}")

    def _ensure_topic_exists(self):
        """Create the topic if it doesn't exist."""
        admin_client = AdminClient({"bootstrap.servers": self.bootstrap_servers})

        # Check existing topics
        metadata = admin_client.list_topics(timeout=10)
        if self.topic in metadata.topics:
            print(f"Topic '{self.topic}' already exists")
            return

        # Create topic
        new_topic = NewTopic(
            self.topic,
            num_partitions=3,  # Allow parallel consumption
            replication_factor=1,  # Single broker for local dev
        )

        futures = admin_client.create_topics([new_topic])

        for topic, future in futures.items():
            try:
                future.result()
                print(f"Created topic: {topic}")
            except Exception as e:
                print(f"Failed to create topic {topic}: {e}")

    def send_delivery(self, delivery: DeliveryEvent):
        """
        Send a single delivery event to Kafka.

        Args:
            delivery: DeliveryEvent to send
        """
        if not self.producer:
            raise RuntimeError("Producer not connected. Call connect() first.")

        # Serialize to JSON
        message = json.dumps(delivery.to_dict())

        # Use match_id as partition key for ordering within a match
        key = delivery.match_id

        self.producer.produce(
            topic=self.topic,
            key=key,
            value=message,
            callback=self._delivery_callback,
        )

        # Trigger delivery reports
        self.producer.poll(0)

    def stream_match(
        self,
        parser: CricsheetParser,
        match_file: Path,
        simulate_live: bool = False,
        delay_ms: int = 100,
    ):
        """
        Stream all deliveries from a single match.

        Args:
            parser: CricsheetParser instance
            match_file: Path to the match JSON file
            simulate_live: If True, add delay between deliveries
            delay_ms: Delay in milliseconds between deliveries
        """
        for delivery in parser.parse_match(match_file):
            self.send_delivery(delivery)

            if simulate_live:
                time.sleep(delay_ms / 1000)

    def stream_all_matches(
        self,
        data_dir: Path,
        limit: Optional[int] = None,
        batch_size: int = 1000,
    ):
        """
        Stream deliveries from all matches in a directory.

        Args:
            data_dir: Directory containing Cricsheet JSON files
            limit: Optional limit on number of matches
            batch_size: Flush producer every N messages
        """
        parser = CricsheetParser(data_dir)
        match_files = parser.list_matches()

        if limit:
            match_files = match_files[:limit]

        print(f"Streaming {len(match_files)} matches to Kafka...")

        total_deliveries = 0
        start_time = time.time()

        for idx, match_file in enumerate(match_files, start=1):
            try:
                match_deliveries = 0
                for delivery in parser.parse_match(match_file):
                    self.send_delivery(delivery)
                    match_deliveries += 1
                    total_deliveries += 1

                    # Periodic flush
                    if total_deliveries % batch_size == 0:
                        self.producer.flush()
                        elapsed = time.time() - start_time
                        rate = total_deliveries / elapsed
                        print(
                            f"Progress: {total_deliveries} deliveries, "
                            f"{rate:.0f}/sec, Match {idx}/{len(match_files)}"
                        )

            except Exception as e:
                print(f"Error processing {match_file.name}: {e}")
                continue

        # Final flush
        self.producer.flush()

        elapsed = time.time() - start_time
        print(f"\nStreaming complete!")
        print(f"Total deliveries: {total_deliveries}")
        print(f"Successful: {self._delivery_count}")
        print(f"Failed: {self._error_count}")
        print(f"Time: {elapsed:.1f}s ({total_deliveries / elapsed:.0f}/sec)")

    def close(self):
        """Close the producer connection."""
        if self.producer:
            self.producer.flush()
            print("Producer closed")


def run_historical_ingestion(
    data_dir: Path = None,
    limit: Optional[int] = None,
):
    """
    Run historical data ingestion from Cricsheet files.

    Args:
        data_dir: Directory containing JSON files
        limit: Optional limit on matches to process
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent.parent / "data" / "raw" / "t20s_json"

    producer = CricketDeliveryProducer()

    try:
        producer.connect()
        producer.stream_all_matches(data_dir, limit=limit)
    finally:
        producer.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stream Cricsheet data to Kafka")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directory containing Cricsheet JSON files",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of matches to process",
    )

    args = parser.parse_args()
    run_historical_ingestion(data_dir=args.data_dir, limit=args.limit)

"""
Kafka Consumer for Bronze Layer
Consumes delivery events and writes to PostgreSQL Bronze layer
"""

import json
import signal
import sys
from datetime import datetime
from typing import Optional

from confluent_kafka import Consumer, KafkaError, KafkaException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()


class BronzeLayerConsumer:
    """
    Kafka consumer that writes raw delivery events to Bronze layer.

    Stores the original JSON payload without transformation
    for data lineage and replayability.
    """

    def __init__(
        self,
        bootstrap_servers: str = None,
        topic: str = None,
        group_id: str = None,
        db_url: str = None,
    ):
        """
        Initialize the consumer.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Kafka topic to consume
            group_id: Consumer group ID
            db_url: PostgreSQL connection URL (sync driver)
        """
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self.topic = topic or settings.kafka_topic_deliveries
        self.group_id = group_id or settings.kafka_consumer_group

        # Use sync driver for consumer (psycopg2)
        self.db_url = db_url or settings.database_url.replace(
            "postgresql+asyncpg", "postgresql"
        )

        self.consumer_config = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,  # Manual commit for reliability
        }

        self.consumer: Optional[Consumer] = None
        self.engine = None
        self.Session = None
        self._running = False
        self._message_count = 0
        self._error_count = 0

    def connect(self):
        """Connect to Kafka and PostgreSQL."""
        # Kafka consumer
        self.consumer = Consumer(self.consumer_config)
        self.consumer.subscribe([self.topic])
        print(f"Subscribed to topic: {self.topic}")

        # PostgreSQL (sync for consumer)
        self.engine = create_engine(self.db_url, pool_size=5, max_overflow=10)
        self.Session = sessionmaker(bind=self.engine)

        # Ensure Bronze table exists
        self._create_bronze_table()

        print(f"Connected to database")

    def _create_bronze_table(self):
        """Create the Bronze layer table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS bronze_deliveries (
            id SERIAL PRIMARY KEY,
            match_id VARCHAR(50) NOT NULL,
            raw_payload JSONB NOT NULL,
            kafka_topic VARCHAR(100) NOT NULL,
            kafka_partition INTEGER,
            kafka_offset BIGINT,
            ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

            -- Index for efficient queries
            CONSTRAINT bronze_deliveries_unique UNIQUE (kafka_topic, kafka_partition, kafka_offset)
        );

        -- Index on match_id for dbt transformations
        CREATE INDEX IF NOT EXISTS idx_bronze_match_id ON bronze_deliveries(match_id);

        -- Index on ingested_at for incremental processing
        CREATE INDEX IF NOT EXISTS idx_bronze_ingested_at ON bronze_deliveries(ingested_at);
        """

        with self.engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()

        print("Bronze table ready")

    def _insert_to_bronze(
        self,
        match_id: str,
        payload: dict,
        topic: str,
        partition: int,
        offset: int,
    ):
        """Insert a delivery event to Bronze layer."""
        insert_sql = """
        INSERT INTO bronze_deliveries (match_id, raw_payload, kafka_topic, kafka_partition, kafka_offset)
        VALUES (:match_id, :raw_payload, :kafka_topic, :kafka_partition, :kafka_offset)
        ON CONFLICT (kafka_topic, kafka_partition, kafka_offset) DO NOTHING
        """

        with self.engine.connect() as conn:
            conn.execute(
                text(insert_sql),
                {
                    "match_id": match_id,
                    "raw_payload": json.dumps(payload),
                    "kafka_topic": topic,
                    "kafka_partition": partition,
                    "kafka_offset": offset,
                },
            )
            conn.commit()

    def consume_batch(self, batch_size: int = 100, timeout: float = 1.0):
        """
        Consume a batch of messages.

        Args:
            batch_size: Maximum messages to consume in one batch
            timeout: Poll timeout in seconds

        Returns:
            Number of messages consumed
        """
        messages_consumed = 0

        while messages_consumed < batch_size:
            msg = self.consumer.poll(timeout=timeout)

            if msg is None:
                break

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition, not an error
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    self._error_count += 1
                    continue

            try:
                # Parse message
                value = json.loads(msg.value().decode("utf-8"))
                match_id = value.get("match_id", "unknown")

                # Write to Bronze layer
                self._insert_to_bronze(
                    match_id=match_id,
                    payload=value,
                    topic=msg.topic(),
                    partition=msg.partition(),
                    offset=msg.offset(),
                )

                messages_consumed += 1
                self._message_count += 1

            except (json.JSONDecodeError, Exception) as e:
                print(f"Error processing message: {e}")
                self._error_count += 1
                # Log to dead letter queue in production
                continue

        # Commit offsets after batch
        if messages_consumed > 0:
            self.consumer.commit()

        return messages_consumed

    def run(self, batch_size: int = 100):
        """
        Run the consumer continuously.

        Args:
            batch_size: Messages per batch before commit
        """
        self._running = True

        # Handle graceful shutdown
        def signal_handler(sig, frame):
            print("\nShutdown signal received...")
            self._running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print(f"Consumer running. Press Ctrl+C to stop.")
        print(f"Consuming from topic: {self.topic}")

        try:
            while self._running:
                consumed = self.consume_batch(batch_size=batch_size)

                if consumed > 0:
                    print(
                        f"Processed {consumed} messages. "
                        f"Total: {self._message_count}, Errors: {self._error_count}"
                    )

        except KeyboardInterrupt:
            pass
        finally:
            self.close()

    def close(self):
        """Close consumer and database connections."""
        if self.consumer:
            self.consumer.close()
            print("Consumer closed")

        if self.engine:
            self.engine.dispose()
            print("Database connection closed")

        print(
            f"Final stats: {self._message_count} processed, {self._error_count} errors"
        )


def run_bronze_consumer():
    """Run the Bronze layer consumer."""
    consumer = BronzeLayerConsumer()

    try:
        consumer.connect()
        consumer.run()
    except Exception as e:
        print(f"Consumer error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_bronze_consumer()

import json
import time
import random
import os
import glob
from datetime import datetime
from kafka import KafkaProducer

# Kafka Configuration
KAFKA_BROKER = "localhost:29092"
TOPIC_NAME = "live_match_deliveries"


def get_kafka_producer():
    """Initializes and returns a Kafka Producer."""
    # Convert payload to bytes
    return KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def match_deliveries_generator(file_path):
    """
    Generator that parses a Cricsheet JSON file and yields individual deliveries
    without loading the entire match state logic into memory.
    """
    with open(file_path, "r") as f:
        match_data = json.load(f)

    info = match_data.get("info", {})
    innings = match_data.get("innings", [])

    match_context = {
        "match_type": info.get("match_type"),
        "teams": info.get("teams"),
        "venue": info.get("venue"),
        "date": info.get("dates", [""])[0],
        "file_id": os.path.basename(file_path),
    }

    for inning in innings:
        team = inning.get("team")
        overs = inning.get("overs", [])

        for over_data in overs:
            over_num = over_data.get("over")
            deliveries = over_data.get("deliveries", [])

            for ball_num, delivery in enumerate(deliveries):
                # Flatten some base structures
                payload = {
                    "match_context": match_context,
                    "inning_team": team,
                    "over": over_num,
                    "ball": ball_num + 1,
                    "delivery_details": delivery,
                    # Append the dynamic execution timestamp!
                    "ingestion_timestamp": datetime.utcnow().isoformat(),
                }
                yield payload


def simulate_live_match(file_path, producer, delay_range=(45, 60)):
    """Runs the simulation, pushing events to Kafka with delays."""
    print(f"Starting simulation for match: {os.path.basename(file_path)}")

    delivery_gen = match_deliveries_generator(file_path)

    for delivery_event in delivery_gen:
        # Push to Kafka
        producer.send(TOPIC_NAME, value=delivery_event)

        print(
            f"Sent: Over {delivery_event['over']}.{delivery_event['ball']} "
            f"({delivery_event['inning_team']}) - "
            f"Batter: {delivery_event['delivery_details'].get('batter')} - "
            f"Timestamp: {delivery_event['ingestion_timestamp']}"
        )

        # Inject delay
        sleep_time = random.uniform(*delay_range)
        print(f"Waiting for {sleep_time:.2f} seconds before next delivery...")
        time.sleep(sleep_time)


if __name__ == "__main__":
    producer = get_kafka_producer()

    # Path to our T20 data from the project root
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    t20_dir = os.path.join(
        project_root,
        "Data",
        "t20s_male_json",
    )

    # Find all JSON files
    json_files = glob.glob(os.path.join(t20_dir, "*.json"))

    if not json_files:
        print(f"No JSON files found in {t20_dir}")
        exit(1)

    # Pick a tournament match at random to simulate
    target_match = random.choice(json_files)

    try:
        # For realistic: delay_range=(45, 60). For dev/test: delay_range=(1, 3).
        # User requested realistic delay:
        simulate_live_match(target_match, producer, delay_range=(45, 60))
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    finally:
        producer.flush()
        producer.close()

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json
from kafka import KafkaConsumer
import asyncio

app = FastAPI(title="Live Match API")

KAFKA_BROKER = "localhost:29092"
TOPIC_NAME = "live_match_deliveries"


def get_kafka_consumer():
    """Initializes and returns a Kafka Consumer."""
    return KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset="latest",  # Get only new messages
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )


async def event_stream():
    """Generator that consumes Kafka messages and yields them as Server-Sent Events (SSE)."""
    consumer = get_kafka_consumer()
    print("API connected to Kafka. Waiting for live deliveries...")

    try:
        for message in consumer:
            data = message.value
            # Yield the message in SSE format
            yield f"data: {json.dumps(data)}\n\n"
            # Yield control back to the event loop so other requests aren't blocked
            await asyncio.sleep(0)
    finally:
        consumer.close()


@app.get("/api/v1/live-match")
async def live_match_stream():
    """
    Endpoint that streams live deliveries directly from Kafka to the frontend.
    Clients can connect to this endpoint using an EventSource (SSE).
    """
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Crickplay Live Match Simulator API! Connect to /api/v1/live-match to stream data."
    }

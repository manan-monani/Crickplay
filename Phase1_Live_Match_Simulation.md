# Phase 1: Live Match Simulation & Data Ingestion

This document outlines the architecture and operational guide for the **Live Match Simulation** layer of the Cricket Analytics SaaS Project. The goal of this phase is to take historical, static JSON data from Cricsheet and realistically simulate a live T20 cricket match.

## 🏗️ Architecture Overview

The system transitions batch data into a resilient, event-driven streaming pipeline using the following core components:

1. **Apache Kafka (Message Broker):** Acts as the high-throughput, low-latency core of the streaming architecture. It decouples the producer (data origin) from the consumer (downstream processing or API).
2. **Producer Application (`src/producer/simulator.py`):** A custom Python script that mimics a live match.
3. **Consumer / API Layer (`src/api/main.py`):** A FastAPI service that subscribes to the Kafka stream and serves the real-time data to clients.

---

## ⚙️ How It Works (Component Breakdown)

### 1. Infrastructure (Docker)
The Kafka cluster is spun up locally using Docker Compose (`docker-compose.yml`). It consists of:
*   **Zookeeper:** Manages the Kafka cluster state.
*   **Kafka Broker:** Hosted on `localhost:29092` (internal `9092`). It stores our streams in a topic called `live_match_deliveries`.

### 2. The Producer (`src/producer/simulator.py`)
The producer is designed to be highly memory-efficient and realistic:
*   **Generator Pattern:** Instead of loading an entire innings' worth of JSON into memory, it uses Python generators (`yield`) to process and emit one delivery at a time.
*   **Execution Timestamp Injection:** As it extracts a historical delivery, it injects an `execution_timestamp` natively, tricking downstream systems into treating this data as a live, happening-now event.
*   **Pacing Mechanism:** To mimic the actual pace of a live T20 game, the script utilizes an engineered delay (randomized between 45 and 60 seconds) between each published message, mimicking bowler run-ups, fielding changes, and strategic timeouts.

### 3. The Real-Time API (`src/api/main.py`)
Since standard REST API request/response paradigms are ill-suited for continuous live updates, we utilized **Server-Sent Events (SSE)** via FastAPI.
*   The API acts as a Kafka Consumer.
*   It continuously listens to the `live_match_deliveries` topic.
*   When a client (like a web browser or future React frontend) calls the `/api/v1/live-match` endpoint, the API keeps the HTTP connection open and pushes new deliveries to the client the absolute millisecond they are generated.

---

## 🚀 How to Run the Simulation

To see the live match simulation in action, follow these steps using two separate terminal windows.

### Step 1: Start the Kafka Infrastructure
Open your first terminal and start the Docker containers:
```powershell
docker-compose up -d
```
*(You can verify the containers are running using the `docker ps` command).*

### Step 2: Start the Producer (The Match Simulator)
In the same terminal, activate the Python virtual environment and start the simulator to begin pushing balls to Kafka:
```powershell
.\venv\Scripts\activate
python src\producer\simulator.py
```
*You will see terminal output showing deliveries being processed every 45-60 seconds.*

### Step 3: Start the Consumer API
Open a **second** terminal, activate the virtual environment, and start the FastAPI server:
```powershell
.\venv\Scripts\activate
uvicorn src.api.main:app --reload --port 8000
```

### Step 4: View the Live Stream
Open your web browser and navigate to:
**http://localhost:8000/api/v1/live-match**

Alternatively, you could consume the endpoint programmatically. Because it uses Server-Sent Events (SSE), the browser window will stay "loading" and new JSON ball data will periodically append to the screen in real-time, perfectly synced with your producer.

---

## ⏭️ Next Steps: The Medallion Architecture

Now that the simulated live stream is buffered stably inside Kafka, the next phase focuses on Storage and Processing:
*   **Bronze Layer:** Implement a sink that dumps these raw JSON streams from Kafka directly into a Data Lake (like S3) for immutable raw storage.
*   **Silver Layer:** Implement an ELT (Extract, Load, Transform) job (e.g., using Apache Spark or Databricks) to read the Bronze data via CDC, flatten the JSON, and standardize player names.
*   **Gold Layer:** Aggregate the Silver data into a Star Schema (`fact_delivery`, `dim_player`) ready for the Machine Learning models and BI Dashboards.
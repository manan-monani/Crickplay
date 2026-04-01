# Crickplay Data Pipeline Documentation

This document describes the complete data pipeline architecture, from live match simulation through the Medallion Architecture to the Gold layer star schema.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CRICKPLAY DATA PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  DATA SOURCES    │     │    STREAMING     │     │  MEDALLION ARCH  │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ • Cricsheet JSON │     │                  │     │                  │
│ • Synthetic Data │────▶│  Apache Kafka    │────▶│  Bronze Layer    │
│ • Live APIs      │     │  (Port 29092)    │     │  (Raw Parquet)   │
│ • Monte Carlo    │     │                  │     │                  │
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
                                                           ▼
                         ┌──────────────────┐     ┌──────────────────┐
                         │  GOLD LAYER      │     │  SILVER LAYER    │
                         │  (Star Schema)   │◀────│  (ELT Cleansed)  │
                         │                  │     │                  │
                         │ • dim_player     │     │ • Flattened JSON │
                         │ • dim_venue      │     │ • Player IDs     │
                         │ • dim_date       │     │ • Standardized   │
                         │ • dim_match      │     │                  │
                         │ • fact_delivery  │     │                  │
                         │ • fact_summary   │     │                  │
                         └──────────────────┘     └──────────────────┘
```

---

## Pipeline Modes

### 1. Streaming Mode (Real-time)

**Use Case**: Live match simulation, real-time analytics

```
Producer → Kafka → Bronze → Silver → Gold (continuous)
```

**Start Command**:
```bash
# Terminal 1: Start Kafka
docker-compose up -d

# Terminal 2: Start Pipeline Orchestrator (streaming mode)
python -m src.pipeline.orchestrator --mode streaming

# Terminal 3: Start Live Match Simulator
streamlit run src/dashboard/match_control.py --server.port 2424
```

### 2. Batch Mode (Historical)

**Use Case**: Initial data load, backfill operations

```
JSON Files → Bronze → Silver → Gold (scheduled/manual)
```

**Start Command**:
```bash
python -m src.pipeline.orchestrator --mode batch
```

---

## Component Details

### 1. Data Sources

#### Cricsheet Historical Data
- **Location**: `Data/t20s_male_json/`, `Data/ipl_json/`, `Data/odis_male_json/`
- **Format**: JSON files (one per match)
- **Volume**: 3,235+ T20 matches, 1,500+ ODI matches

#### Synthetic Data Generator
- **Module**: `src/synthetic/`
- **Method**: Monte Carlo simulation
- **Use**: Generate matches for emerging teams (Italy, Canada, Oman)

### 2. Live Match Simulator

#### Producer Script
- **Module**: `src/producer/simulator.py`
- **Features**:
  - Generator pattern (memory efficient)
  - Configurable delay (0.5s - 60s per ball)
  - Adds execution timestamp
  - Team/player filtering

#### Streamlit Dashboard
- **Location**: `src/dashboard/match_control.py`
- **Port**: 2424
- **Features**:
  - Team selection
  - Historical match filtering
  - Simulation speed control
  - Real-time monitoring

### 3. Apache Kafka

#### Topics
| Topic | Purpose | Retention |
|-------|---------|-----------|
| `cricket-live-data` | Live match deliveries | 7 days |
| `match-events` | Match lifecycle events | 30 days |

#### Configuration
```python
from src.config.ports import KAFKA_CONFIG

bootstrap_servers = "localhost:29092"
topic = "cricket-live-data"
```

### 4. Bronze Layer (Raw Ingestion)

- **Path**: `src/storage/lakehouse/bronze/`
- **Format**: Parquet (partitioned by date)
- **Schema**: Schema-on-read (preserves raw JSON)
- **Module**: `src/medallion/bronze/kafka_sink.py`

**Partitioning**:
```
bronze/
├── raw_deliveries/
│   └── 2024/
│       └── 01/
│           └── 15/
│               └── batch_20240115_143022_abc12345.parquet
```

### 5. Silver Layer (Cleansed & Conformed)

- **Path**: `src/storage/lakehouse/silver/`
- **Format**: Parquet (columnar, compressed)
- **Module**: `src/medallion/silver/transformer.py`

**Transformations**:
- Flatten nested JSON arrays
- Standardize player IDs
- Handle cricket-specific nulls (extras = null → legal delivery)
- Add derived fields (is_four, is_six, is_dot_ball)
- Incremental CDC (Change Data Capture)

### 6. Gold Layer (Star Schema)

- **Path**: `src/storage/lakehouse/gold/`
- **Format**: Parquet (one table per entity)
- **Module**: `src/medallion/gold/schema.py`

---

## Star Schema Design

### Dimension Tables

#### dim_player
| Column | Type | Description |
|--------|------|-------------|
| player_id | VARCHAR(12) | Primary key (MD5 hash) |
| player_name | VARCHAR | Canonical name |
| alternative_names | JSON | Name variations |
| batting_style | VARCHAR | RHB, LHB |
| bowling_style | VARCHAR | RF, OB, SLA, etc. |
| primary_role | VARCHAR | Batter, Bowler, All-rounder |
| total_runs_scored | INT | Career runs |
| total_wickets_taken | INT | Career wickets |

#### dim_venue
| Column | Type | Description |
|--------|------|-------------|
| venue_id | VARCHAR(12) | Primary key (MD5 hash) |
| venue_name | VARCHAR | Full venue name |
| city | VARCHAR | City location |
| country | VARCHAR | Country |
| pitch_type | VARCHAR | spin-friendly, pace-friendly, flat |
| boundary_size | VARCHAR | small, medium, large |

#### dim_date
| Column | Type | Description |
|--------|------|-------------|
| date_key | VARCHAR(10) | YYYY-MM-DD format |
| full_date | VARCHAR | "January 15, 2024" |
| year | INT | Year number |
| month | INT | Month number |
| day | INT | Day number |
| day_of_week | INT | 0=Monday, 6=Sunday |
| day_name | VARCHAR | Monday, Tuesday, etc. |
| is_weekend | BOOL | Weekend flag |
| quarter | INT | Q1-Q4 |
| week_of_year | INT | ISO week number |
| tournament_phase | VARCHAR | Group, Super8, Final |

#### dim_match_context
| Column | Type | Description |
|--------|------|-------------|
| match_context_id | VARCHAR | Primary key |
| match_id | VARCHAR | External match ID |
| match_type | VARCHAR | T20, ODI, Test |
| match_date | VARCHAR | Match date |
| venue_id | VARCHAR | FK to dim_venue |
| team_a | VARCHAR | First team |
| team_b | VARCHAR | Second team |
| toss_winner | VARCHAR | Toss winning team |
| toss_decision | VARCHAR | bat, field |
| winner | VARCHAR | Winning team |

### Fact Tables

#### fact_delivery (Grain: one row per ball)
| Column | Type | Description |
|--------|------|-------------|
| delivery_key | VARCHAR | Surrogate key |
| match_context_id | VARCHAR | FK to dim_match_context |
| batter_id | VARCHAR | FK to dim_player |
| bowler_id | VARCHAR | FK to dim_player |
| venue_id | VARCHAR | FK to dim_venue |
| inning | INT | 1 or 2 |
| over | INT | Over number |
| ball | INT | Ball number |
| runs_batter | INT | Runs off bat |
| runs_extras | INT | Extra runs |
| runs_total | INT | Total runs |
| is_four | BOOL | Boundary flag |
| is_six | BOOL | Six flag |
| is_wicket | BOOL | Wicket flag |
| wicket_kind | VARCHAR | caught, bowled, etc. |
| **win_probability_delta** | FLOAT | Change in win probability |
| **tenant_id** | VARCHAR | Multi-tenancy (RLS) |
| event_timestamp | VARCHAR | When event occurred |

#### fact_match_summary (Grain: one row per match)
| Column | Type | Description |
|--------|------|-------------|
| match_key | VARCHAR | Surrogate key |
| match_context_id | VARCHAR | FK to dim_match_context |
| first_innings_runs | INT | 1st innings total |
| second_innings_runs | INT | 2nd innings total |
| total_fours | INT | Match total fours |
| total_sixes | INT | Match total sixes |
| run_rate_first | FLOAT | 1st innings run rate |
| run_rate_second | FLOAT | 2nd innings run rate |
| **tenant_id** | VARCHAR | Multi-tenancy (RLS) |

---

## Running the Pipeline

### Prerequisites
```bash
# Start Docker services
docker-compose up -d

# Verify Kafka is running
docker-compose ps
```

### Automatic Pipeline (Recommended)

The Pipeline Orchestrator automatically chains all stages:

```bash
# Streaming mode (continuous)
python -m src.pipeline.orchestrator --mode streaming

# Batch mode (process existing data)
python -m src.pipeline.orchestrator --mode batch
```

### Manual Stage-by-Stage

If you prefer manual control:

```bash
# Step 1: Start producer (generates Kafka messages)
python -m src.producer.simulator

# Step 2: Run Bronze sink (Kafka → Bronze)
python -m src.medallion.bronze.kafka_sink

# Step 3: Run Silver transformer (Bronze → Silver)
python -m src.medallion.silver.transformer --mode incremental

# Step 4: Run Gold aggregator (Silver → Gold)
python -m src.medallion.gold.schema
```

---

## Monitoring & Verification

### Check Kafka Topics
```bash
docker exec -it crickplay_kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

### View Bronze Layer
```python
from src.medallion.bronze.kafka_sink import BronzeReader

reader = BronzeReader()
files = reader.list_files()
print(f"Bronze files: {len(files)}")
```

### View Silver Layer
```python
from src.medallion.silver.transformer import SilverTransformer

transformer = SilverTransformer()
stats = transformer.get_statistics()
print(stats)
```

### View Gold Layer
```python
from src.medallion.gold.schema import StarSchemaBuilder

builder = StarSchemaBuilder()
print(f"Players: {len(builder._players)}")
print(f"Venues: {len(builder._venues)}")
```

---

## Dashboard Access

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| Match Control | http://localhost:2424 | Configure & start simulations |
| Kafka UI | http://localhost:8081 | View Kafka topics (planned) |
| Analytics | http://localhost:8501 | Data analytics (planned) |

---

## FAQ

### Does data flow automatically?

**Yes**, when using the Pipeline Orchestrator in streaming mode. The orchestrator:
1. Consumes from Kafka topic
2. Writes to Bronze layer
3. Triggers Silver transformation
4. Updates Gold star schema

### How do I see the pipeline status?

The Match Control Dashboard (port 2424) includes a Pipeline Status tab showing:
- Messages consumed
- Files written per layer
- Processing latency

### What if I want to reprocess all data?

```bash
# Reset Silver CDC checkpoint and reprocess
python -m src.medallion.silver.transformer --mode full
```

### How do I add a new team?

1. Add team profile in `src/synthetic/team_profiles.py`
2. Generate synthetic matches with Monte Carlo
3. Run through pipeline

---

## Change Data Capture (CDC)

Crickplay implements a robust CDC system to enable efficient incremental processing and prevent duplicate data. The system is located in `src/medallion/cdc.py`.

### CDC Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      CDC MANAGER                                │
├────────────────────────────────────────────────────────────────┤
│  FileTracker        │  RecordDeduplicator  │  WatermarkManager  │
│  ─────────────      │  ──────────────────  │  ─────────────────  │
│  • File hashes      │  • Record hashes     │  • Timestamp HWM    │
│  • Processing       │  • SHA-256 hash of   │  • Partition marks  │
│    status           │    delivery identity │  • Offset tracking  │
│  • Batch tracking   │  • Session + persisted│  • Kafka offsets   │
└────────────────────────────────────────────────────────────────┘
```

### CDC Components

#### 1. FileTracker
Tracks which files have been processed to prevent reprocessing:
- Uses MD5 hash of file path + size + modification time
- Stores processing metadata (records processed, duration)
- Supports pattern matching for pending file discovery

#### 2. RecordDeduplicator
Prevents duplicate delivery records using content-based hashing:
- Hashes key identity fields: match_id, inning, over, ball, batter, bowler
- Uses SHA-256 truncated to 16 characters
- Maintains session cache + persisted checkpoint

#### 3. WatermarkManager
Tracks high-water marks for incremental queries:
- Stores last processed timestamp per data source
- Supports Kafka offset tracking per partition
- Enables `SELECT * WHERE timestamp > watermark` pattern

### Using CDC

```python
from src.medallion.cdc import CDCManager, CDCConfig

# Initialize with enhanced features
cdc = CDCManager(CDCConfig(
    checkpoint_dir="src/storage/lakehouse/cdc",
    enable_file_tracking=True,
    enable_record_dedup=True,
    enable_watermarks=True,
))

# File-level CDC
pending = cdc.get_pending_files("bronze/", "*.parquet")
for file in pending:
    process_file(file)
    cdc.mark_file_processed(file)

# Record-level deduplication
for record in incoming_records:
    if not cdc.is_duplicate(record):
        store(record)
        cdc.mark_seen(record)

# Watermark-based incremental
hwm = cdc.get_watermark("kafka_consumer")
new_data = query_since(hwm)
cdc.update_watermark("kafka_consumer", latest_timestamp)

# Persist state
cdc.commit()
```

### CDC Checkpoints

Checkpoint files are stored in `src/storage/lakehouse/cdc/`:
- `file_tracker.json` - File processing history
- `record_hashes.json` - Seen delivery hashes
- `watermarks.json` - High-water marks

### CDC CLI Commands

```bash
# View CDC statistics
python -m src.medallion.cdc --mode stats

# List pending files
python -m src.medallion.cdc --mode pending -d src/storage/lakehouse/bronze

# Reset all CDC state (caution!)
python -m src.medallion.cdc --mode reset
```

### Integration with Silver Layer

The Silver transformer automatically uses CDC:

```bash
# Incremental mode (default) - only new files
python -m src.medallion.silver.transformer --mode incremental

# With enhanced CDC (record-level dedup)
python -m src.medallion.silver.transformer --mode incremental --enhanced-cdc

# Full reprocess (resets CDC first)
python -m src.medallion.silver.transformer --mode full
```

---

## API Integration

### Where to Put Live Match API Data

If you have a live match API that generates data, you have two integration points:

#### Option 1: Push to Kafka (Recommended)
Your API produces messages to Kafka, and the orchestrator consumes them:

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="localhost:29092",
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def on_live_delivery(delivery_data):
    producer.send("cricket-live-data", delivery_data)
```

#### Option 2: Direct Pipeline Call
Call the orchestrator's process method directly:

```python
from src.pipeline.orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator()

def on_live_delivery(delivery_data):
    orchestrator.process_single_message(delivery_data)
```

#### Current API Location
The FastAPI implementation is at `src/api/main.py`:
- Port 8001 (see PORTS.md)
- SSE streaming for frontend
- Currently consumes from Kafka (read-only)

To enable auto-flow, run the Pipeline Orchestrator alongside your API:
```bash
# Terminal 1: API server
uvicorn src.api.main:app --port 8001

# Terminal 2: Pipeline (processes and stores data)
python -m src.pipeline.orchestrator --mode streaming
```

---

## File Structure

```
src/
├── config/
│   └── ports.py              # Port registry
├── producer/
│   └── simulator.py          # Kafka producer
├── dashboard/
│   └── match_control.py      # Streamlit dashboard
├── pipeline/
│   └── orchestrator.py       # Auto-pipeline coordinator
├── medallion/
│   ├── bronze/
│   │   └── kafka_sink.py     # Kafka → Bronze
│   ├── silver/
│   │   ├── transformer.py    # Bronze → Silver
│   │   └── player_identity.py
│   └── gold/
│       └── schema.py         # Star schema
└── storage/
    └── lakehouse/
        ├── bronze/           # Raw Parquet
        ├── silver/           # Cleansed data
        └── gold/             # Star schema tables
```

# Phase 2: Synthetic Data Generation & Medallion Architecture

This document outlines the implementation of **Synthetic Data Generation** and the **Medallion Architecture** for the Cricket Analytics SaaS Project.

## 🏗️ Architecture Overview

### Synthetic Data Generation
Monte Carlo simulations generate realistic match data for teams with limited historical records (Italy, Canada, Oman, etc.) to prepare for 2026 World Cup scenarios.

### Medallion Architecture (Data Lakehouse)
Three-layer data processing pipeline:

```
┌──────────────────────────────────────────────────────────────┐
│                      KAFKA STREAM                            │
│              (live_match_deliveries topic)                   │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    🥉 BRONZE LAYER                           │
│  • Raw JSON/Parquet storage                                  │
│  • Immutable append-only archive                             │
│  • Schema-on-read capability                                 │
│  Path: src/storage/lakehouse/bronze/                         │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    🥈 SILVER LAYER                           │
│  • Flattened tabular format                                  │
│  • Standardized player identities                            │
│  • Cricket-specific null handling                            │
│  • CDC for incremental processing                            │
│  Path: src/storage/lakehouse/silver/                         │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    🥇 GOLD LAYER                             │
│  • Star Schema (fact + dimension tables)                     │
│  • Optimized for ML/BI queries                               │
│  • Pre-aggregated metrics                                    │
│  Path: src/storage/lakehouse/gold/                           │
└──────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
src/
├── producer/
│   └── simulator.py              # Kafka producer (Phase 1)
├── api/
│   └── main.py                   # SSE API (Phase 1)
├── synthetic/
│   ├── __init__.py
│   ├── team_profiles.py          # Team strength definitions
│   ├── monte_carlo.py            # Simulation engine
│   └── generator.py              # Match data generator CLI
├── medallion/
│   ├── __init__.py
│   ├── bronze/
│   │   ├── __init__.py
│   │   └── kafka_sink.py         # Kafka → Bronze storage
│   ├── silver/
│   │   ├── __init__.py
│   │   └── transformer.py        # ELT pipeline
│   └── gold/
│       ├── __init__.py
│       └── schema.py             # Star Schema builder
└── storage/
    └── lakehouse/
        ├── bronze/               # Raw Parquet/JSON files
        ├── silver/               # Cleansed tabular data
        └── gold/                 # Star Schema tables
```

---

## 🚀 Quick Start

### Prerequisites
```powershell
# Ensure Kafka is running
docker-compose up -d

# Install dependencies
pip install -r requirements.txt
```

### 1. Generate Synthetic Data

```powershell
# List available teams
python -m src.synthetic.generator --list-teams

# Generate matches for a specific team
python -m src.synthetic.generator --team Italy --matches 10

# Generate World Cup 2026 scenarios
python -m src.synthetic.generator --world-cup --output src/storage/lakehouse/bronze/synthetic
```

### 2. Run Bronze Layer (Kafka Sink)

```powershell
# Stream mode (continuous)
python -m src.medallion.bronze.kafka_sink --mode stream

# Batch mode (one-time)
python -m src.medallion.bronze.kafka_sink --mode batch --timeout 30

# Check statistics
python -m src.medallion.bronze.kafka_sink --mode stats
```

### 3. Run Silver Layer (ELT Transformer)

```powershell
# Incremental processing (only new files)
python -m src.medallion.silver.transformer --mode incremental

# Full refresh
python -m src.medallion.silver.transformer --mode full

# Check statistics
python -m src.medallion.silver.transformer --mode stats
```

### 4. Build Gold Layer (Star Schema)

```powershell
# Build Star Schema from Silver data
python -m src.medallion.gold.schema --mode build

# Check statistics
python -m src.medallion.gold.schema --mode stats
```

---

## 📊 Data Models

### Fact Tables

#### `fact_delivery`
One row per ball delivered in a match.

| Column | Type | Description |
|--------|------|-------------|
| delivery_key | STRING | Surrogate key |
| match_context_id | STRING | FK to dim_match_context |
| batter_id | STRING | FK to dim_player |
| bowler_id | STRING | FK to dim_player |
| venue_id | STRING | FK to dim_venue |
| over | INT | Over number (0-19) |
| ball | INT | Ball in over (1-6) |
| runs_batter | INT | Runs scored off bat |
| runs_extras | INT | Extra runs (wides, byes, etc.) |
| is_wicket | BOOLEAN | Wicket taken flag |
| is_four | BOOLEAN | Boundary flag |
| is_six | BOOLEAN | Six flag |

#### `fact_match_summary`
Aggregated match-level metrics.

| Column | Type | Description |
|--------|------|-------------|
| match_key | STRING | Surrogate key |
| venue_id | STRING | FK to dim_venue |
| first_innings_runs | INT | First innings total |
| second_innings_runs | INT | Second innings total |
| total_fours | INT | Total boundaries |
| total_sixes | INT | Total sixes |
| win_margin | STRING | Victory margin |

### Dimension Tables

#### `dim_player`
Player attributes and career statistics.

| Column | Type | Description |
|--------|------|-------------|
| player_id | STRING | Primary key (canonical ID) |
| player_name | STRING | Display name |
| batting_style | STRING | Right/Left hand |
| bowling_style | STRING | Fast/Spin type |
| total_runs_scored | INT | Career runs |
| total_wickets_taken | INT | Career wickets |

#### `dim_venue`
Venue characteristics.

| Column | Type | Description |
|--------|------|-------------|
| venue_id | STRING | Primary key |
| venue_name | STRING | Full venue name |
| pitch_type | STRING | batting/bowling/spin-friendly |
| avg_first_innings_score | FLOAT | Historical average |

#### `dim_match_context`
Match conditions and metadata.

| Column | Type | Description |
|--------|------|-------------|
| match_context_id | STRING | Primary key |
| match_type | STRING | T20/ODI/Test |
| toss_winner | STRING | Team that won toss |
| toss_decision | STRING | bat/field |
| winner | STRING | Match winner |

---

## 🧪 Testing the Pipeline

### End-to-End Test

```powershell
# Terminal 1: Start Kafka infrastructure
docker-compose up -d

# Terminal 2: Start the producer (simulates live match)
python src\producer\simulator.py

# Terminal 3: Run Bronze sink
python -m src.medallion.bronze.kafka_sink --mode stream --max-messages 50

# Terminal 4: Run Silver transformer
python -m src.medallion.silver.transformer --mode incremental

# Terminal 5: Build Gold layer
python -m src.medallion.gold.schema --mode build
```

### Verify Data Flow

```powershell
# Check Bronze layer
python -m src.medallion.bronze.kafka_sink --mode stats

# Check Silver layer
python -m src.medallion.silver.transformer --mode stats

# Check Gold layer
python -m src.medallion.gold.schema --mode stats
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| KAFKA_BROKER | localhost:29092 | Kafka broker address |
| KAFKA_TOPIC | live_match_deliveries | Topic name |
| BRONZE_PATH | src/storage/lakehouse/bronze | Bronze layer path |
| SILVER_PATH | src/storage/lakehouse/silver | Silver layer path |
| GOLD_PATH | src/storage/lakehouse/gold | Gold layer path |

---

## ⏭️ Next Steps

1. **ML Feature Store**: Extract features from Gold layer for model training
2. **Real-time Analytics**: Connect BI tools to Gold layer
3. **Player Performance Models**: Build predictive models using dimensional data
4. **Match Outcome Prediction**: Use historical patterns for live predictions

# Crickplay Port Registry

This document provides a centralized registry of all ports used by services in the Crickplay project. All ports are defined in `src/config/ports.py` for programmatic access.

## Port Allocation Summary

| Port | Service | Category | Description |
|------|---------|----------|-------------|
| 22181 | Zookeeper (External) | Infrastructure | Kafka coordination service |
| 2181 | Zookeeper (Internal) | Infrastructure | Internal Docker network |
| 29092 | Kafka (External) | Infrastructure | Message broker |
| 9092 | Kafka (Internal) | Infrastructure | Internal Docker network |
| 5432 | PostgreSQL | Infrastructure | Primary database |
| 6379 | Redis | Infrastructure | Cache/session store |
| 8000 | FastAPI Main | Application | Primary API endpoint |
| 8001 | Live Match API | Application | Live match streaming |
| 2424 | Match Control Dashboard | Frontend | Streamlit simulator control |
| 8501 | Analytics Dashboard | Frontend | Streamlit analytics |
| 3000 | Web Frontend | Frontend | Next.js/React frontend |
| 8010 | Bronze Pipeline | Pipeline | Bronze layer service |
| 8011 | Silver Pipeline | Pipeline | Silver layer service |
| 8012 | Gold Pipeline | Pipeline | Gold layer service |
| 9090 | Prometheus | Monitoring | Metrics collection |
| 3001 | Grafana | Monitoring | Metrics visualization |
| 8081 | Kafka UI | Monitoring | Kafka topic browser |

---

## Detailed Service Documentation

### Infrastructure Services

#### Zookeeper
- **External Port**: 22181
- **Internal Port**: 2181
- **Purpose**: Kafka cluster coordination and configuration management
- **Docker Service**: `zookeeper`

#### Apache Kafka
- **External Port**: 29092
- **Internal Port**: 9092
- **Purpose**: Message broker for live match event streaming
- **Docker Service**: `kafka`
- **Topics**: `cricket-live-data`, `match-events`

#### PostgreSQL
- **Port**: 5432
- **Purpose**: Primary relational database for user data, API state
- **Note**: Not yet configured in docker-compose

#### Redis
- **Port**: 6379
- **Purpose**: Caching, session management, real-time pub/sub
- **Note**: Not yet configured in docker-compose

---

### Application Services

#### FastAPI Main API
- **Port**: 8000
- **Purpose**: Primary REST API endpoint
- **Endpoints**: `/health`, `/matches`, `/predictions`
- **Start Command**: `uvicorn src.api.main:app --port 8000`

#### Live Match API
- **Port**: 8001
- **Purpose**: Server-Sent Events (SSE) stream for live match data
- **Endpoints**: `/stream/live`, `/stream/{match_id}`
- **Start Command**: `uvicorn src.api.main:app --port 8001`

---

### Frontend Services

#### Match Control Dashboard (Streamlit)
- **Port**: 2424
- **Purpose**: Control panel for live match simulator
- **Features**: Team selection, player filtering, simulation speed control
- **Start Command**: `streamlit run src/dashboard/match_control.py --server.port 2424`

#### Analytics Dashboard (Streamlit)
- **Port**: 8501
- **Purpose**: Data analytics and visualization
- **Note**: Planned for Phase 3

#### Web Frontend
- **Port**: 3000
- **Purpose**: User-facing web application
- **Note**: Planned for Phase 4

---

### Pipeline Services

#### Bronze Pipeline Service
- **Port**: 8010
- **Purpose**: Raw data ingestion from Kafka to Bronze layer
- **Format**: Parquet files in `src/storage/lakehouse/bronze/`

#### Silver Pipeline Service
- **Port**: 8011
- **Purpose**: ELT transformation (cleansing, flattening)
- **Format**: Cleansed Parquet in `src/storage/lakehouse/silver/`

#### Gold Pipeline Service
- **Port**: 8012
- **Purpose**: Star schema aggregation
- **Format**: Dimensional tables in `src/storage/lakehouse/gold/`

---

### Monitoring Services

#### Prometheus
- **Port**: 9090
- **Purpose**: Metrics collection and alerting
- **Note**: Planned for Phase 4

#### Grafana
- **Port**: 3001
- **Purpose**: Metrics visualization dashboards
- **Note**: Planned for Phase 4

#### Kafka UI
- **Port**: 8081
- **Purpose**: Visual Kafka topic browser and management
- **Note**: Planned addition to docker-compose

---

## Programmatic Access

All ports are available programmatically via the `ports` module:

```python
from src.config.ports import PORTS, get_port, get_service_url, KAFKA_CONFIG

# Get specific port
api_port = get_port("fastapi_main")  # Returns 8000

# Get full service URL
api_url = get_service_url("fastapi_main")  # Returns "http://localhost:8000"

# Kafka configuration
kafka_bootstrap = KAFKA_CONFIG["bootstrap_servers"]  # "localhost:29092"
```

---

## Adding New Services

When adding a new service:

1. **Update `src/config/ports.py`**:
   ```python
   PORTS = {
       ...
       "new_service": 8XXX,
   }
   ```

2. **Update this document** with the new service details

3. **If using Docker**, update `docker-compose.yml`:
   ```yaml
   services:
     new-service:
       ports:
         - "8XXX:8XXX"
   ```

4. **Verify no conflicts** by reviewing this registry

---

## Port Range Conventions

| Range | Purpose |
|-------|---------|
| 2000-2999 | User-facing dashboards |
| 3000-3999 | Frontend applications |
| 5000-5999 | Databases |
| 6000-6999 | Caches (Redis) |
| 8000-8099 | Main APIs |
| 8010-8099 | Pipeline services |
| 8500-8599 | Streamlit apps |
| 9000-9999 | Monitoring |
| 22000-29999 | Infrastructure (Kafka, Zookeeper) |

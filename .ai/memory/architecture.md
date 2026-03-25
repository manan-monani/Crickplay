# Crickplay System Architecture

> T20 Cricket Match Outcome Prediction SaaS Platform | 2026 ICC Men's T20 World Cup Edition

---

## Overview

**Project Name:** Crickplay
**Type:** Real-time Sports Analytics SaaS Platform
**Target:** 2026 ICC Men's T20 World Cup (co-hosted by India & Sri Lanka)
**Tech Stack:** Python (FastAPI) + Next.js + PostgreSQL + Kafka + XGBoost + LangGraph

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  Coach Dashboard │  │ Bettor Dashboard│  │   Broadcaster Dashboard    │  │
│  │  (Professional)  │  │ (Professional)  │  │      (Enterprise)          │  │
│  └────────┬─────────┘  └────────┬────────┘  └─────────────┬──────────────┘  │
│           │                     │                         │                  │
│  ┌────────┴─────────────────────┴─────────────────────────┴──────────────┐  │
│  │                     Next.js 14 App Router (TypeScript)                │  │
│  │  - React Query for data fetching                                      │  │
│  │  - Zustand for state management                                       │  │
│  │  - WebSocket for real-time updates                                    │  │
│  │  - Recharts for data visualization                                    │  │
│  └───────────────────────────────────────┬───────────────────────────────┘  │
└──────────────────────────────────────────┼──────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (NGINX)                                  │
│  ┌──────────┐  ┌───────────────┐  ┌──────────┐  ┌────────────────────────┐  │
│  │   SSL    │  │  Subdomain    │  │   Rate   │  │   Tenant Header       │  │
│  │Termination│  │   Routing    │  │ Limiting │  │   Injection           │  │
│  └──────────┘  └───────────────┘  └──────────┘  └────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BACKEND SERVICE LAYER                                  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     FastAPI Application                                 │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │     Auth     │  │   Analytics  │  │   AI Chat    │                  │ │
│  │  │   Service    │  │    Service   │  │   Service    │                  │ │
│  │  │  (JWT+RBAC)  │  │ (Statistics) │  │ (LangGraph)  │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │   Narrative  │  │   WebSocket  │  │   Stripe     │                  │ │
│  │  │   Service    │  │   Handler    │  │  Webhooks    │                  │ │
│  │  │  (GenAI)     │  │ (Real-time)  │  │  (Payments)  │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     ML Inference (Ray Serve)                           │ │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐           │ │
│  │  │  XGBoost Win   │  │ Score Forecast │  │ Player Cluster │           │ │
│  │  │  Probability   │  │  (Regression)  │  │  (K-Means)     │           │ │
│  │  │  + SHAP        │  │                │  │                │           │ │
│  │  └────────────────┘  └────────────────┘  └────────────────┘           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
┌──────────────────────┐  ┌───────────────────────┐  ┌─────────────────────┐
│    EVENT STREAMING   │  │      DATA LAYER       │  │   VECTOR STORE      │
│                      │  │                       │  │                     │
│  ┌────────────────┐  │  │  ┌─────────────────┐  │  │  ┌───────────────┐  │
│  │     Kafka      │  │  │  │   PostgreSQL    │  │  │  │   ChromaDB    │  │
│  │  - deliveries  │  │  │  │  (Main DB)      │  │  │  │  (RAG Docs)   │  │
│  │  - match_events│  │  │  │  + RLS          │  │  │  │               │  │
│  │  - dlq         │  │  │  └─────────────────┘  │  │  └───────────────┘  │
│  └────────────────┘  │  │                       │  │                     │
│  ┌────────────────┐  │  │  ┌─────────────────┐  │  └─────────────────────┘
│  │   Zookeeper    │  │  │  │     Redis       │  │
│  └────────────────┘  │  │  │  (Cache + WP)   │  │
└──────────────────────┘  │  │  (Sessions)     │  │
                          │  └─────────────────┘  │
                          └───────────────────────┘
```

---

## Medallion Data Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA WAREHOUSE LAYERS                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ BRONZE LAYER (Raw)                                                   │    │
│  │ - bronze_deliveries (raw_payload JSONB, kafka_offset, ingested_at)  │    │
│  │ - Source: Kafka consumer → PostgreSQL                                │    │
│  └───────────────────────────────────┬─────────────────────────────────┘    │
│                                      │ dbt transformation                    │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ SILVER LAYER (Cleaned)                                               │    │
│  │ - stg_deliveries (flattened, typed, standardized)                   │    │
│  │ - stg_match_info (venue, toss, teams, tournament)                   │    │
│  └───────────────────────────────────┬─────────────────────────────────┘    │
│                                      │ dbt transformation                    │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ GOLD LAYER (Star Schema)                                             │    │
│  │                                                                      │    │
│  │  DIMENSION TABLES:                                                   │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────────┐   │    │
│  │  │ dim_player │ │ dim_venue  │ │  dim_date  │ │dim_match_context│   │    │
│  │  │ (SCD2)     │ │(pitch data)│ │(date spine)│ │(toss, phase)    │   │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └─────────────────┘   │    │
│  │                                                                      │    │
│  │  FACT TABLES:                                                        │    │
│  │  ┌─────────────────────┐  ┌──────────────────────┐                  │    │
│  │  │   fact_delivery     │  │  fact_match_summary  │                  │    │
│  │  │ - one row per ball  │  │ - one row per match  │                  │    │
│  │  │ - win_prob_delta    │  │ - aggregated stats   │                  │    │
│  │  │ - tenant_id (RLS)   │  │ - tenant_id (RLS)    │                  │    │
│  │  └─────────────────────┘  └──────────────────────┘                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend
| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Runtime | Python | 3.11+ | Primary language |
| Framework | FastAPI | latest | REST API + WebSocket |
| ORM | SQLAlchemy 2.0 | async | Database operations |
| Migrations | Alembic | latest | Schema management |
| Validation | Pydantic v2 | strict | Request/response models |
| Auth | python-jose + passlib | - | JWT + password hashing |
| Rate Limiting | slowapi | - | Tier-based rate limits |

### Frontend
| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | Next.js | 14 | App Router + SSR |
| Language | TypeScript | 5+ | Type safety |
| Styling | Tailwind CSS | 3 | Utility-first CSS |
| Components | shadcn/ui | - | UI components |
| Data Fetching | TanStack Query | v5 | Caching + mutations |
| State | Zustand | - | Global state |
| Charts | Recharts | - | Data visualization |
| WebSocket | socket.io-client | - | Real-time updates |

### Data Engineering
| Component | Technology | Purpose |
|-----------|------------|---------|
| Streaming | Apache Kafka | Real-time event bus |
| ETL | dbt-postgres | Bronze → Silver → Gold |
| Data Quality | dbt-elementary | Data observability |
| Data Source | Cricsheet JSON | Historical match data |

### Machine Learning
| Component | Technology | Purpose |
|-----------|------------|---------|
| Primary Model | XGBoost | Win probability classification |
| Interpretability | SHAP | Feature importance explanations |
| Experiment Tracking | MLflow | Model versioning |
| Hyperparameter | Optuna | Bayesian optimization |
| Model Serving | Ray Serve | Low-latency inference |
| Feature Engineering | pandas + numpy | Feature computation |

### GenAI Stack
| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM | Claude (Anthropic) | Text generation |
| Orchestration | LangGraph | Agentic workflows |
| Framework | LangChain | Tool orchestration |
| Vector Store | ChromaDB | Document embeddings |
| Embeddings | Claude Haiku | Vector generation |

### Infrastructure
| Component | Technology | Purpose |
|-----------|------------|---------|
| Container | Docker | Containerization |
| Orchestration | Docker Compose / K8s | Service orchestration |
| Database | PostgreSQL 14+ | Primary data store |
| Cache | Redis 7 | Sessions + WP cache |
| Reverse Proxy | NGINX | SSL + subdomain routing |
| CI/CD | GitHub Actions | Automated pipelines |

### Payments & Monitoring
| Component | Technology | Purpose |
|-----------|------------|---------|
| Payments | Stripe | Subscription billing |
| Error Tracking | Sentry | Error monitoring |
| Metrics | Prometheus + Grafana | Observability |
| Security Audit | OWASP ZAP | Vulnerability scanning |

---

## Directory Structure

```
Crickplay/
├── AGENT.md                         # AI agent instructions
├── CLAUDE.md                        # Primary Claude instructions
├── README.md                        # Project overview
├── Makefile                         # Build automation
├── docker-compose.yml               # Local development stack
├── docker-compose.prod.yml          # Production stack
│
├── backend/                         # Python FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint
│   │   ├── config.py                # Settings (pydantic-settings)
│   │   ├── dependencies.py          # Dependency injection
│   │   │
│   │   ├── routers/                 # API route handlers
│   │   │   ├── auth.py              # /auth/* endpoints
│   │   │   ├── matches.py           # /matches/* endpoints
│   │   │   ├── players.py           # /players/* endpoints
│   │   │   ├── venues.py            # /venues/* endpoints
│   │   │   ├── ai_chat.py           # /ai/chat endpoint
│   │   │   └── stripe_webhook.py    # /stripe/webhook
│   │   │
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── tenant.py
│   │   │   ├── subscription.py
│   │   │   └── analytics.py
│   │   │
│   │   ├── schemas/                 # Pydantic schemas
│   │   │   ├── auth.py
│   │   │   ├── match.py
│   │   │   ├── player.py
│   │   │   └── ai.py
│   │   │
│   │   ├── services/                # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── ml_service.py
│   │   │   └── narrative_service.py
│   │   │
│   │   └── db/                      # Database utilities
│   │       ├── session.py           # Async session factory
│   │       └── tenant.py            # RLS tenant context
│   │
│   ├── ingestion/                   # Kafka producers/consumers
│   │   ├── producer.py              # Live match simulator
│   │   └── consumer.py              # Bronze layer sink
│   │
│   ├── ml/                          # Machine learning
│   │   ├── features.py              # FeatureEngineer class
│   │   ├── train.py                 # Model training script
│   │   └── inference.py             # Ray Serve endpoint
│   │
│   ├── genai/                       # LangGraph agents
│   │   ├── tools/
│   │   │   ├── text_to_sql.py       # SQL generation tool
│   │   │   └── vector_search.py     # RAG retrieval tool
│   │   └── graph.py                 # LangGraph StateGraph
│   │
│   ├── dbt/                         # dbt project
│   │   ├── models/
│   │   │   ├── bronze/
│   │   │   ├── silver/
│   │   │   └── gold/
│   │   ├── seeds/                   # Manual CSV data
│   │   └── dbt_project.yml
│   │
│   ├── alembic/                     # DB migrations
│   │   └── versions/
│   │
│   ├── tests/                       # Pytest tests
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   │
│   ├── scripts/                     # Utility scripts
│   │   └── download_cricsheet.py
│   │
│   ├── pyproject.toml               # Python dependencies (uv/poetry)
│   ├── requirements.txt             # Pip requirements
│   └── .env.example
│
├── frontend/                        # Next.js frontend
│   ├── app/                         # App Router pages
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── dashboard/
│   │   │   ├── coach/
│   │   │   ├── bettor/
│   │   │   ├── broadcaster/
│   │   │   └── ai-chat/
│   │   └── pricing/
│   │
│   ├── components/                  # React components
│   │   ├── ui/                      # shadcn components
│   │   ├── charts/                  # Recharts wrappers
│   │   └── shared/                  # Common components
│   │
│   ├── lib/                         # Utilities
│   │   ├── api.ts                   # Axios instance
│   │   └── auth.ts                  # Auth helpers
│   │
│   ├── stores/                      # Zustand stores
│   │   └── auth-store.ts
│   │
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── .env.example
│
├── infra/                           # Infrastructure
│   ├── docker/
│   │   ├── backend.Dockerfile
│   │   ├── frontend.Dockerfile
│   │   └── ml-inference.Dockerfile
│   ├── k8s/                         # Kubernetes manifests
│   │   ├── deployments/
│   │   ├── services/
│   │   └── ingress/
│   └── nginx/
│       └── nginx.conf               # Subdomain routing
│
├── data/                            # Data directory (gitignored)
│   ├── raw/                         # Cricsheet ZIPs
│   ├── bronze/                      # Raw JSON partitions
│   ├── documents/                   # Unstructured docs for RAG
│   └── models/                      # MLflow artifacts
│
├── docs/                            # Documentation
│   ├── features/
│   ├── api/
│   ├── setup.md
│   └── deployment.md
│
├── .ai/                             # AI agent context
│   ├── memory/
│   │   ├── architecture.md          # This file
│   │   ├── decisions.md
│   │   └── tasks.md
│   ├── agents/
│   ├── skills/
│   ├── prompts/
│   └── hooks/
│
├── .github/
│   ├── workflows/
│   │   └── ci.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── copilot-instructions.md
│
└── .vscode/
    └── mcp.json                     # MCP server configuration
```

---

## Data Flow

### Real-time Win Probability Flow

```
1. Kafka receives ball-by-ball delivery event
2. Consumer writes to Bronze layer (PostgreSQL JSONB)
3. dbt runs incremental Silver → Gold transformation
4. ML Service extracts features from current match state
5. XGBoost model predicts win probability
6. SHAP explains top 3 contributing factors
7. Result cached in Redis (wp:{match_id})
8. WebSocket broadcasts to connected clients
9. If delta > 5%, NarrativeService generates commentary
```

### Agentic RAG Query Flow

```
1. User submits natural language query via /ai/chat
2. LangGraph router analyzes intent:
   - Statistical query → text_to_sql tool
   - Qualitative query → vector_search tool
   - Hybrid → parallel tool execution
3. Text-to-SQL: Claude generates SQL → sanitize → execute
4. Vector Search: embed query → ChromaDB similarity search
5. Synthesizer combines tool outputs
6. Claude generates grounded final answer
7. Response includes: answer, sources, tool_used
```

---

## Security Architecture

### Authentication
- JWT-based (access: 15min TTL, refresh: 7 days)
- Refresh tokens stored in Redis
- Password hashing with bcrypt via passlib

### Authorization (RBAC)
| Role | Access Level | Features |
|------|-------------|----------|
| fan | Basic | 5 AI queries/day, basic stats |
| professional | Standard | Full analytics, unlimited AI |
| enterprise | Premium | Custom narratives, API access |
| admin | Full | System administration |

### Multi-Tenancy
- PostgreSQL Row-Level Security (RLS)
- Tenant ID injected via `SET app.current_tenant`
- Subdomain routing: `teama.crickplay.com` → tenant isolation

### Rate Limiting
| Tier | Limit |
|------|-------|
| Fan | 100 req/hour |
| Professional | 1000 req/hour |
| Enterprise | Unlimited |

---

## ML Model Details

### Win Probability Classifier

**Algorithm:** XGBoost (binary classification)
**Target:** Team batting first wins (0/1)

**Feature Vector (25 dimensions):**

| Category | Features |
|----------|----------|
| Match State | balls_remaining, wickets_in_hand, run_lead_or_deficit |
| Run Rates | current_run_rate, required_run_rate, run_rate_differential |
| Player Strength | batter_rolling_sr_last10, bowler_rolling_economy_last10, team_elo_score |
| Context | venue_avg_first_innings, toss_venue_impact, pitch_phase, is_knockout |

**Train/Val/Test Split:** Time-based (pre-2023/2023/2024) — never shuffle

**Evaluation Metrics:**
- Primary: Log-loss
- Secondary: Brier score, calibration curve

---

## Environment Variables

### Backend (.env)
```
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/crickplay
REDIS_URL=redis://localhost:6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Auth
SECRET_KEY=<random-256-bit-key>
JWT_SECRET=<random-256-bit-key>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# AI
ANTHROPIC_API_KEY=sk-ant-xxx

# Payments
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxx
```

---

## Deployment Environments

| Environment | URL | Branch | Purpose |
|-------------|-----|--------|---------|
| Development | localhost:3000 / :8000 | develop | Local dev |
| Staging | staging.crickplay.com | staging | Pre-production |
| Production | crickplay.com | main | Live |

---

## Critical Implementation Notes

1. **RLS from Day One:** Implement PostgreSQL Row-Level Security before loading Gold layer data
2. **Time-based ML Split:** Always split by date — never shuffle cricket data
3. **Kafka Generator Pattern:** Yield one delivery at a time to avoid OOM on ~7,470 matches
4. **SHAP is Required:** Enterprise clients need explainability — not a post-launch feature
5. **Subdomain Routing Early:** Validate NGINX + Next.js middleware before first tenant
6. **Stripe Webhooks:** Test with `stripe listen --forward-to` before go-live

---

**Last Updated:** 2026-03-25
**Phase:** Foundation Setup (Week 1-2)

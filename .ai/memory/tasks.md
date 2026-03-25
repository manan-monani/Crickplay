# Task Tracker

> Persistent task tracking for AI agents. Update this file as tasks progress.

---

## Quick Status

| Status | Count |
|--------|-------|
| Done | 16 |
| In Progress | 0 |
| Todo | 2 |
| Backlog | 12 |

**Last Updated:** 2026-03-25 18:20
**Current Focus:** Phase 5 (ML Pipeline) preparation

---

## In Progress

### [TASK-010] Gold Layer Dimension Tables
- **Priority:** P1
- **Size:** L
- **Phase:** 3
- **Started:** 2026-03-25
- **Branch:** `develop`
- **Description:** Create dbt Gold layer dimension models
- **Progress:**
  - [ ] dim_player.sql (with SCD Type 2)
  - [ ] dim_venue.sql (with pitch data seeds)
  - [ ] dim_date.sql (date spine)
  - [ ] dim_match_context.sql (toss, phase, weather)
  - [ ] schema.yml with tests

### [TASK-011] Gold Layer Fact Tables
- **Priority:** P1
- **Size:** L
- **Phase:** 3
- **Started:** 2026-03-25
- **Branch:** `develop`
- **Description:** Create dbt Gold layer fact models
- **Progress:**
  - [ ] fact_delivery.sql (one row per ball, incremental)
  - [ ] fact_match_summary.sql (aggregated per match)
  - [ ] Add tenant_id column
  - [ ] schema.yml with tests
  - [ ] Verify aggregation integrity

---

## Done

### [TASK-001] Update architecture.md
- **Completed:** 2026-03-25
- **Summary:** Full system architecture with medallion data architecture, tech stack, directory structure

### [TASK-002] Create Claude memory files
- **Completed:** 2026-03-25
- **Summary:** Created memory files for persistent context across sessions

### [TASK-003] Set up complete project structure
- **Completed:** 2026-03-25
- **Summary:** Monorepo with /backend, /frontend, /infra, /data, /docs + all config files

### [TASK-004] Docker Compose Local Stack
- **Completed:** 2026-03-25
- **Summary:** docker-compose.yml with postgres, redis, kafka, zookeeper, kafka-ui, mlflow

### [TASK-005] Cricsheet Parser & Data Download
- **Completed:** 2026-03-25
- **Summary:** CricsheetParser class with generator pattern + download_cricsheet.py script

### [TASK-006] Kafka Producer & Consumer
- **Completed:** 2026-03-25
- **Summary:** CricketDeliveryProducer (batch/live modes) + BronzeLayerConsumer (→ PostgreSQL JSONB)

### [TASK-007] Silver Layer dbt Models
- **Completed:** 2026-03-25
- **Summary:** stg_deliveries.sql and stg_match_info.sql with schema tests

### [TASK-008] FastAPI App Skeleton
- **Completed:** 2026-03-25
- **Summary:** FastAPI with config, health endpoint, CORS, GZip middleware

---

## Todo

### [TASK-012] Multi-Tenancy: Row-Level Security
- **Priority:** P0
- **Size:** M
- **Phase:** 3
- **Description:** Add tenant_id to Gold tables + PostgreSQL RLS policies + FastAPI middleware
- **Dependencies:** TASK-010, TASK-011
- **Critical Note:** Must be done BEFORE loading Gold layer data

### [TASK-013] FastAPI Auth System
- **Priority:** P1
- **Size:** L
- **Phase:** 4
- **Description:** JWT auth (register, login, refresh), RBAC (fan/professional/enterprise/admin), rate limiting (slowapi)
- **Dependencies:** TASK-012

### [TASK-014] Core API Endpoints
- **Priority:** P1
- **Size:** L
- **Phase:** 4
- **Description:** /matches, /matches/{id}/win-probability, /players/{id}/stats, /venues/{id}/analytics, /tournaments/{id}/leaderboard
- **Dependencies:** TASK-013

### [TASK-015] Database Session & Tenant Utilities
- **Priority:** P1
- **Size:** M
- **Phase:** 4
- **Description:** Async session factory, tenant context injection per request
- **Dependencies:** TASK-012

### [TASK-016] Alembic Initial Migration
- **Priority:** P1
- **Size:** S 
- **Phase:** 4
- **Description:** Users, tenants, subscriptions tables + properly configure alembic.ini
- **Dependencies:** TASK-012

### [TASK-017] Virtual Environment Verification
- **Priority:** P1
- **Size:** S
- **Phase:** 1
- **Description:** Ensure backend venv has all required packages installed and working

---

## Backlog

### Phase 5 — ML Pipeline
- [TASK-020] Feature Engineering Pipeline (25-dim vector)
- [TASK-021] XGBoost Model Training + Optuna HPO
- [TASK-022] SHAP Integration + Real-time Inference
- [TASK-023] Additional ML Models (regressor, clustering, association rules)

### Phase 6 — GenAI
- [TASK-030] Text-to-SQL Agent Tool
- [TASK-031] Vector Search Tool (ChromaDB)
- [TASK-032] LangGraph Agentic Router
- [TASK-033] Dynamic Narrative Generation

### Phase 7 — Frontend
- [TASK-040] Next.js App Setup + Shared Components
- [TASK-041] Coach Dashboard
- [TASK-042] Bettor & Broadcaster Dashboards
- [TASK-043] AI Chat Interface

### Phase 8 — Deployment
- [TASK-050] Dockerize All Services
- [TASK-051] Kubernetes Deployment (AWS EKS)
- [TASK-052] Stripe Payment Integration
- [TASK-053] Security Hardening & Monitoring

---

## Priority Guide

| Priority | Description | Response |
|----------|-------------|----------|
| P0 | Critical/Blocking | Immediate |
| P1 | High - Core work | Current session |
| P2 | Medium - Enhancement | Next available |
| P3 | Low - Nice to have | When time permits |

## Size Guide

| Size | Complexity | Typical Time |
|------|------------|--------------|
| S | Simple, single file | < 1 hour |
| M | Moderate, few files | 1-4 hours |
| L | Complex, many files | 4-8 hours |
| XL | Very complex | 1+ days |

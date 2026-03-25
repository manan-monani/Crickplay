# Architectural Decisions Record

> Document significant technical decisions made during development.

---

## Decision Log

### [ADR-001] Monorepo Structure
**Date:** 2026-03-25
**Status:** Accepted

**Context:**
Need to organize backend, frontend, and infrastructure code for a SaaS platform with multiple services.

**Options Considered:**
1. **Monorepo with /backend, /frontend, /infra directories**
   - Pros: Single version control, easier cross-cutting changes, shared tooling
   - Cons: Larger repo size, potential CI complexity

2. **Polyrepo (separate repos)**
   - Pros: Independent versioning, smaller clone sizes
   - Cons: Harder to synchronize changes, dependency management overhead

**Decision:**
Use monorepo structure. The platform has tight coupling between services and shared schema definitions make monorepo more practical.

**Consequences:**
- Positive: Single PR can update API contract + frontend
- Positive: Shared CI/CD pipeline configuration
- Neutral: Need proper .gitignore to manage repo size

---

### [ADR-002] PostgreSQL Row-Level Security for Multi-Tenancy
**Date:** 2026-03-25
**Status:** Accepted

**Context:**
Platform serves multiple tenants (teams, broadcasters) who must be isolated from each other's data.

**Options Considered:**
1. **Application-layer filtering (WHERE tenant_id = ?)**
   - Pros: Simple to implement
   - Cons: Error-prone, requires vigilance on every query

2. **PostgreSQL RLS with session variables**
   - Pros: Database-enforced isolation, cannot be bypassed by app bugs
   - Cons: Slightly more complex setup

3. **Separate databases per tenant**
   - Pros: Complete isolation
   - Cons: Operational overhead, harder to run cross-tenant analytics

**Decision:**
Use PostgreSQL RLS with `SET app.current_tenant` injection in FastAPI middleware. Provides strong isolation with minimal overhead.

**Consequences:**
- Positive: Zero risk of cross-tenant data leakage from application bugs
- Positive: Single database simplifies operations
- Neutral: Must remember to enable RLS on new tables

---

### [ADR-003] Medallion Architecture (Bronze/Silver/Gold)
**Date:** 2026-03-25
**Status:** Accepted

**Context:**
Need to transform raw Cricsheet JSON into analytics-ready star schema.

**Options Considered:**
1. **Direct ETL to star schema**
   - Pros: Fewer layers
   - Cons: Hard to debug, no data lineage

2. **Medallion architecture with dbt**
   - Pros: Clear data lineage, incremental processing, testable layers
   - Cons: More tables, dbt learning curve

**Decision:**
Use medallion architecture: Bronze (raw JSONB) → Silver (cleaned/typed) → Gold (star schema). Implemented with dbt-postgres.

**Consequences:**
- Positive: Clear data quality gates at each layer
- Positive: dbt tests catch issues early
- Positive: Can replay transformations if logic changes

---

### [ADR-004] XGBoost with SHAP for Win Probability
**Date:** 2026-03-25
**Status:** Accepted

**Context:**
Need interpretable win probability predictions for enterprise clients (team coaches, broadcasters).

**Options Considered:**
1. **Deep learning (LSTM/Transformer)**
   - Pros: Can capture sequential patterns
   - Cons: Black box, slow inference, hard to explain

2. **XGBoost with SHAP explanations**
   - Pros: Fast inference, built-in SHAP support, interpretable
   - Cons: May miss complex temporal patterns

3. **Logistic regression (baseline)**
   - Pros: Fully interpretable
   - Cons: Limited modeling capacity

**Decision:**
Use XGBoost with TreeSHAP. Enterprise requirement for explainability makes this non-negotiable. Performance is adequate for real-time inference.

**Consequences:**
- Positive: Every prediction includes top 3 feature contributions
- Positive: <200ms inference latency via Ray Serve
- Neutral: Must maintain feature engineering pipeline

---

### [ADR-005] LangGraph for Agentic RAG
**Date:** 2026-03-25
**Status:** Accepted

**Context:**
Need to route natural language queries to appropriate data sources (SQL vs vector search).

**Options Considered:**
1. **Simple function calling**
   - Pros: Straightforward
   - Cons: No complex orchestration, no parallel tool calls

2. **LangGraph StateGraph**
   - Pros: Visual graph, parallel execution, checkpointing
   - Cons: Learning curve, more code

3. **Custom router**
   - Pros: Full control
   - Cons: Reinventing the wheel

**Decision:**
Use LangGraph with router → (text_to_sql || vector_search) → synthesizer pattern.

**Consequences:**
- Positive: Clean separation of concerns
- Positive: Can add new tools without changing flow
- Neutral: Dependency on LangGraph ecosystem

---

## Quick Reference

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| 001 | Monorepo Structure | Accepted | 2026-03-25 |
| 002 | PostgreSQL RLS Multi-Tenancy | Accepted | 2026-03-25 |
| 003 | Medallion Architecture | Accepted | 2026-03-25 |
| 004 | XGBoost + SHAP | Accepted | 2026-03-25 |
| 005 | LangGraph Agentic RAG | Accepted | 2026-03-25 |

---

## Categories

### Architecture
- ADR-001: Monorepo Structure
- ADR-003: Medallion Architecture

### Technology
- ADR-004: XGBoost + SHAP
- ADR-005: LangGraph

### Security
- ADR-002: PostgreSQL RLS

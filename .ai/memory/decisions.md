# Architectural Decisions Record

> Document significant technical decisions made during development.

---

## Decision Log

### [ADR-001] Monorepo Structure
**Date:** 2026-03-25
**Status:** Accepted

**Context:**
Need to organize backend, frontend, and infrastructure code for a SaaS platform with multiple services.

**Decision:**
Use monorepo structure with `/backend`, `/frontend`, `/infra`. The platform has tight coupling between services and shared schema definitions make monorepo more practical.

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

**Decision:**
Use LangGraph with router → (text_to_sql || vector_search) → synthesizer pattern.

**Consequences:**
- Positive: Clean separation of concerns
- Positive: Can add new tools without changing flow
- Neutral: Dependency on LangGraph ecosystem

---

### [ADR-006] Google Gemini as LLM Provider
**Date:** 2026-03-25
**Status:** Accepted

**Context:**
Need a reliable LLM for Text-to-SQL, agentic RAG, and narrative generation. Originally considered Anthropic Claude but switched to Google Gemini.

**Decision:**
Use Google Gemini API via `google-generativeai` and `langchain-google-genai` packages. Aligns with Google ecosystem compatibility and API key availability.

**Consequences:**
- Positive: Good integration with LangChain/LangGraph
- Positive: Competitive pricing and performance
- Neutral: Need to handle Gemini-specific prompt formatting

---

### [ADR-007] Python 3.11+ with venv for Backend
**Date:** 2026-03-25
**Status:** Accepted

**Context:**
Need Python dependency management. Options: poetry, uv, pip+venv.

**Decision:**
Use standard `python -m venv` with pip and `requirements.txt`. Simple, universally understood, no extra tooling needed. Virtual env at `backend/.venv/`.

**Consequences:**
- Positive: Zero learning curve, CI/CD compatible
- Positive: requirments.txt works everywhere
- Neutral: No lock file (could add pip-tools if needed)

---

## Quick Reference

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| 001 | Monorepo Structure | Accepted | 2026-03-25 |
| 002 | PostgreSQL RLS Multi-Tenancy | Accepted | 2026-03-25 |
| 003 | Medallion Architecture | Accepted | 2026-03-25 |
| 004 | XGBoost + SHAP | Accepted | 2026-03-25 |
| 005 | LangGraph Agentic RAG | Accepted | 2026-03-25 |
| 006 | Google Gemini LLM | Accepted | 2026-03-25 |
| 007 | Python venv + pip | Accepted | 2026-03-25 |

---

## Categories

### Architecture
- ADR-001: Monorepo Structure
- ADR-003: Medallion Architecture

### Technology
- ADR-004: XGBoost + SHAP
- ADR-005: LangGraph
- ADR-006: Google Gemini
- ADR-007: Python venv

### Security
- ADR-002: PostgreSQL RLS

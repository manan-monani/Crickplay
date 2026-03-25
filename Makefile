# Crickplay Makefile
# Usage: make <target>

.PHONY: help up down logs shell clean backend-install frontend-install test lint

# Default target
help:
	@echo "Crickplay Development Commands"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make up          - Start all services (postgres, redis, kafka)"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - View service logs"
	@echo "  make shell       - Open bash in backend container"
	@echo "  make clean       - Remove all containers and volumes"
	@echo ""
	@echo "Backend:"
	@echo "  make backend-install  - Install Python dependencies"
	@echo "  make backend-dev      - Run FastAPI development server"
	@echo "  make backend-test     - Run backend tests"
	@echo "  make backend-lint     - Run linters (black, isort, flake8)"
	@echo "  make backend-format   - Format code (black, isort)"
	@echo ""
	@echo "Frontend:"
	@echo "  make frontend-install - Install Node.js dependencies"
	@echo "  make frontend-dev     - Run Next.js development server"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate       - Run Alembic migrations"
	@echo "  make db-shell         - Open PostgreSQL shell"
	@echo "  make dbt-run          - Run dbt transformations"
	@echo ""
	@echo "ML:"
	@echo "  make ml-train         - Train ML models"
	@echo ""

# ============================================
# Infrastructure
# ============================================

up:
	docker-compose up -d
	@echo "Services started. Kafka UI at http://localhost:8081"

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec postgres bash

clean:
	docker-compose down -v --remove-orphans
	@echo "All containers and volumes removed"

# ============================================
# Backend
# ============================================

backend-install:
	cd backend && pip install -r requirements.txt -r requirements-dev.txt

backend-dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	cd backend && pytest -v

backend-lint:
	cd backend && black --check . && isort --check-only . && flake8 .

backend-format:
	cd backend && black . && isort .

# ============================================
# Frontend
# ============================================

frontend-install:
	cd frontend && pnpm install

frontend-dev:
	cd frontend && pnpm dev

# ============================================
# Database
# ============================================

db-migrate:
	cd backend && alembic upgrade head

db-shell:
	docker-compose exec postgres psql -U postgres -d crickplay

dbt-run:
	cd backend/dbt && dbt run

dbt-test:
	cd backend/dbt && dbt test

# ============================================
# ML
# ============================================

ml-train:
	cd backend && python -m ml.train

# ============================================
# Development Setup
# ============================================

setup: up backend-install
	@echo "Development environment ready!"
	@echo "Run 'make backend-dev' to start the API server"

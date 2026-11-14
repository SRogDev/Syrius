# Syrius Makefile — Phase 0 targets. Every target below was run on this VM
# except the Docker-dependent ones (no Docker daemon in the sandbox);
# see IMPLEMENTATION_STATUS.md.

.PHONY: install up down migrate dev-api dev-web test lint check slice

slice: ## Run the real CartPole acceptance slice (SQLite, worker CLI)
	uv run --project apps/api python scripts/run_cartpole_slice.py

install: ## Install Python (uv) and JS (pnpm) dependencies
	uv sync
	pnpm install

up: ## Start PostgreSQL via Docker Compose
	docker compose up -d postgres

down: ## Stop the Compose stack
	docker compose down

migrate: ## Apply Alembic migrations (requires Postgres up)
	cd apps/api && uv run alembic upgrade head

dev-api: ## Run the FastAPI API on :8000 (reload)
	cd apps/api && uv run uvicorn syrius_api.main:app --reload --port 8000

dev-web: ## Run the web SPA on :3000 (proxies /api to :8000)
	pnpm --filter syrius-web dev

test: ## Run Python tests and the web production build
	uv run --project apps/api python -m pytest apps/api/tests -q
	uv run --project apps/worker python -m pytest apps/worker/tests -q
	pnpm --filter syrius-web build

lint: ## Ruff (Python) + Biome (TypeScript)
	uv run --project apps/api ruff check apps/api apps/worker
	pnpm exec biome check .

check: lint test ## Lint + test

# Syrius API

FastAPI service for the Syrius RL Engineering Factory.

Phase 0 scope: two health endpoints only.

- `GET /health` — liveness probe.
- `GET /api/v1/health` — versioned health probe used by the web frontend.

Both return real state, including honest PostgreSQL reachability
(`db: ok` / `db: unavailable`, `status: ok` / `status: degraded`).

## Run

```sh
cd apps/api
uv run uvicorn syrius_api.main:app --reload --port 8000
```

## Test

```sh
uv run --project apps/api python -m pytest apps/api/tests -q
```

## Migrate

```sh
make migrate   # from the repo root; requires PostgreSQL up (make up)
```

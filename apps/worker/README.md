# Syrius worker

Background worker for the Syrius RL Engineering Factory.

Phase 0 scope: registration + heartbeat/status CLI only. There is no job
queue or training loop yet — those arrive with Phase 1.

## Commands

```sh
uv run --project apps/worker python -m syrius_worker.main status
uv run --project apps/worker python -m syrius_worker.main heartbeat
```

`status` reports database reachability and whether this worker has
registered; `heartbeat` (re-)registers the worker in the
`worker_registrations` table (created by Alembic migration `0001`).
Both report `db: unavailable` honestly — and exit non-zero — when
PostgreSQL is down or migrations have not been applied.

## Test

```sh
uv run --project apps/worker python -m pytest apps/worker/tests -q
```

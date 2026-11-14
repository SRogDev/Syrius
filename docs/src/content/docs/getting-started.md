---

title: Getting started
description: Install Syrius locally and run the Phase 0 stack.
---

Phase 0 is the repository foundation: the web SPA, the FastAPI service,
the worker CLI and PostgreSQL. Nothing beyond Phase 0 is built yet.

## Prerequisites

- Node.js 24 and [pnpm](https://pnpm.io/) 12
- Python 3.12 and [uv](https://docs.astral.sh/uv/) 0.12
- Docker (for PostgreSQL)

## Install

```sh
git clone https://github.com/SRogDev/Syrius.git
cd Syrius
make install
```

`make install` runs `uv sync` (Python workspace) and `pnpm install`
(TypeScript workspaces).

## Configure

```sh
cp .env.example .env
```

Defaults point at a local PostgreSQL on port 5432 with user/password
`syrius` / `syrius`. No secrets are committed; `.env` is gitignored.

## Start PostgreSQL and run migrations

```sh
make up        # docker compose up -d postgres
make migrate   # alembic upgrade head (creates worker_registrations)
```

## Run the services

In two terminals:

```sh
make dev-api   # FastAPI on http://localhost:8000
make dev-web   # TanStack Start SPA on http://localhost:3000
```

The web home page shows the live API health panel: open
[http://localhost:3000](http://localhost:3000) and check that `status`
is `ok` and `db` is `ok`. If PostgreSQL is down, the API honestly
reports `status: degraded` and `db: unavailable` instead of failing.

## Verify

```sh
make check     # ruff + Biome lint, pytest, web production build
```

## Worker

```sh
uv run --project apps/worker python -m syrius_worker.main status
uv run --project apps/worker python -m syrius_worker.main heartbeat
```

`status` reports whether the database is reachable and whether this
worker has registered; `heartbeat` (re-)registers it. Both exit non-zero
and say so when the database is unavailable.

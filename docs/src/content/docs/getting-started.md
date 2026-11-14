---

title: Getting started
description: Install Syrius locally and run the v0.1 stack (Phases 0–7).
---

Syrius v0.1 is the full backend vertical slice (Phases 0–6) plus the
Four Studios (Phase 5) and the Phase 7 hardening pass: projects, RL
problem specs, Gymnasium environments, PPO training through a real
job queue + worker, independent evaluation, policy export, list
endpoints, training history and artifact download.

## Prerequisites

- Node.js 24 and [pnpm](https://pnpm.io/) 12
- Python 3.12 and [uv](https://docs.astral.sh/uv/) 0.12
- Docker — only for the PostgreSQL path (see below). Without Docker
  you can still run everything on SQLite.

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

## Path A — PostgreSQL via Docker (full stack)

On a machine with a Docker daemon:

```sh
make up        # docker compose up -d postgres
make migrate   # alembic upgrade head (creates worker_registrations + slice tables)
```

In a sandbox without a Docker daemon this stops here: `make up`
fails with `Cannot connect to the Docker daemon` and `make migrate`
fails with connection refused. That is an environment limit, not a
code failure — use Path B instead.

## Path B — SQLite, no Docker (verified path)

Everything — including the real training run — works against a local
SQLite database:

```sh
make slice     # real CartPole run: baseline → PPO 20000 steps →
               # evaluation → export, ~90 s, SQLite + worker CLI
make e2e       # Phase 7 end-to-end acceptance, same shape plus
               # list/history/download assertions
```

Both write measured reports under `var/results/` (gitignored) and
the committed evidence copies live in `docs/evidence/`.

## Run the services

In two terminals:

```sh
make dev-api   # FastAPI on http://localhost:8000
make dev-web   # TanStack Start SPA on http://localhost:3000
```

The web home page shows the live API health panel: open
[http://localhost:3000](http://localhost:3000) and check that `status`
is `ok` and `db` is `ok`. If PostgreSQL is down, the API honestly
reports `status: degraded` and `db: unavailable` instead of failing —
and the data endpoints return 500 (there is no database to read).
Allow 15–30 s for the first API start: importing torch/SB3 is slow.

## Verify

```sh
make check     # ruff + Biome lint, pytest (api 37, worker 4),
               # web production build
pnpm --filter syrius-web test      # Vitest, 30 tests
pnpm --filter syrius-web typecheck # strict TS
pnpm --filter syrius-docs build    # docs build
```

## Worker

```sh
uv run --project apps/worker python -m syrius_worker.main status
uv run --project apps/worker python -m syrius_worker.main heartbeat
```

`status` reports whether the database is reachable and whether this
worker has registered; `heartbeat` (re-)registers it. Both exit non-zero
and say so when the database is unavailable.

## What is not built yet

Auth, paid compute, production deploys, training resume, job
logs/resource usage, scenario comparison, and a department/tasks
model. See `IMPLEMENTATION_STATUS.md` in the repo for the honest
per-item state.

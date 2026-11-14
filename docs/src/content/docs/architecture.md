---

title: Architecture
description: How the Syrius monorepo is put together (Phases 0–6).
---

## Monorepo layout

```text
syrius/
├── apps/
│   ├── web/        TanStack Start SPA (React 19, Tailwind v4)
│   ├── api/        FastAPI + SQLAlchemy + Alembic (Python)
│   └── worker/     Background worker CLI (Python)
├── packages/
│   └── api-client/ OpenAPI-generated TypeScript types
├── scripts/        Acceptance run (CartPole slice), API client generator
├── docs/           Astro Starlight documentation
├── infrastructure/ Dockerfiles + docker-compose.yml
└── tests/          (reserved — app tests live next to their apps)
```

`packages/api-client/src/types.ts` is generated from the API's live
OpenAPI schema (`scripts/gen_api_client.py`) — the first real shared
package, landed with Phases 1–6.

## Principles

- **Fetch by default, persist by intent.** The web reads live state from
  the API; nothing is faked or seeded.
- **Honest health.** Every component reports its real state. A down
  database is `degraded` / `unavailable`, never a green check.
- **One stack per concern.** TypeScript for the web, Python for the API
  and worker, PostgreSQL (self-managed) for durable state.
- **No mocks in acceptance paths.** Skeleton pages say "not yet
  implemented" where that is true.

## Services

| Service  | Entry point                             | Responsibility (Phases 0–6)                                                   |
| -------- | --------------------------------------- | ----------------------------------------------------------------------------- |
| web      | `apps/web`                              | SPA shell, `/` and `/projects` routes, live API health panel                  |
| api      | `apps/api/src/syrius_api/main.py`       | Health + full `/api/v1/` (projects, specs, envs, experiments, eval, policies) |
| worker   | `apps/worker/src/syrius_worker/main.py` | `status` / `heartbeat` CLI + `run` job loop (train/baseline/evaluate/export)  |
| postgres | `docker-compose.yml`                    | PostgreSQL 16, named volume `syrius_pgdata`                                   |

## Backend modules (Phases 1–6)

All under `apps/api/src/syrius_api/`:

| Module            | Responsibility                                                              |
| ----------------- | --------------------------------------------------------------------------- |
| `models.py`       | SQLAlchemy models for all §12 slice entities + audit events                 |
| `rl.py`           | Gymnasium adapter, random baseline, SB3 PPO training, evaluation, packaging |
| `jobs.py`         | Postgres-backed job queue (lease/heartbeat/retry/cancel)                    |
| `executor.py`     | What the worker runs per job kind                                           |
| `tools.py`        | 71 department tool definitions + real CartPole handlers                     |
| `capabilities.py` | EngineeringCapability contract + §13 approval gates                         |
| `workflows.py`    | LangGraph training workflow (StateGraph + MemorySaver)                      |
| `storage.py`      | Local filesystem storage (real) + S3 interface                              |
| `routers.py`      | Versioned `/api/v1/` routes + SSE progress                                  |

The database layer is database-agnostic by design: PostgreSQL is
canonical (Compose + CI), SQLite serves local dev and tests
(`DATABASE_URL=sqlite:///...`). Long work is always a job — the API
never trains inside a request handler.

## What is not built yet

The Four Studios (Phase 5, frontend), auth, and hardening (Phase 7)
belong to later phases. See `IMPLEMENTATION_STATUS.md` at the repo root
for the honest per-item state.

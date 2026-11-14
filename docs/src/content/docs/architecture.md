---

title: Architecture
description: How the Syrius monorepo is put together in Phase 0.
---

## Monorepo layout

```text
syrius/
├── apps/
│   ├── web/        TanStack Start SPA (React 19, Tailwind v4)
│   ├── api/        FastAPI + SQLAlchemy + Alembic (Python)
│   └── worker/     Background worker CLI (Python)
├── docs/           Astro Starlight documentation
├── infrastructure/ Dockerfiles + docker-compose.yml
└── tests/          (reserved — app tests live next to their apps)
```

There is no `packages/` directory in Phase 0: no shared package contains
real code yet. The API client types will be generated from the API's
OpenAPI schema when Phase 1 adds real routes — not before.

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

| Service  | Entry point                             | Responsibility (Phase 0)                                     |
| -------- | --------------------------------------- | ------------------------------------------------------------ |
| web      | `apps/web`                              | SPA shell, `/` and `/projects` routes, live API health panel |
| api      | `apps/api/src/syrius_api/main.py`       | `GET /health`, `GET /api/v1/health` with DB reachability     |
| worker   | `apps/worker/src/syrius_worker/main.py` | `status` / `heartbeat` CLI, registration row in Postgres     |
| postgres | `docker-compose.yml`                    | PostgreSQL 16, named volume `syrius_pgdata`                  |

## What is not built yet

Projects, runs, environments, training (Gymnasium / Stable-Baselines3),
departments, studios, auth and BYOK all belong to Phases 1–7. See
`IMPLEMENTATION_STATUS.md` at the repo root for the honest per-item state.

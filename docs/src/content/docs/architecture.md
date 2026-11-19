---

title: Architecture
description: How the Syrius monorepo is put together (Phases 0–7).
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

| Service  | Entry point                             | Responsibility (Phases 0–7)                                                                                                                                                                                           |
| -------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| web      | `apps/web`                              | SPA shell + Four Studios: Project (`/projects/$projectId?studio=`), Environment (`/episodes/$episodeId`), Experiment (`/experiments/$experimentId`), Evaluation (`/evaluations/$evaluationId`), live API health panel |
| api      | `apps/api/src/syrius_api/main.py`       | Health + full `/api/v1/` (projects, specs, envs, experiments, eval, policies)                                                                                                                                         |
| worker   | `apps/worker/src/syrius_worker/main.py` | `status` / `heartbeat` CLI + `run` job loop (train/baseline/evaluate/export)                                                                                                                                          |
| postgres | `docker-compose.yml`                    | PostgreSQL 16, named volume `syrius_pgdata`                                                                                                                                                                           |

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

## Polygrow integration & compute (2026-11-19 — Roger's directive)

Roger's architectural directive "Rustenwer & Syrius — Architectural
Evolution Toward Polygrow's Intelligence Infrastructure" (2026-11-19) sets
the ecosystem direction. Full audit: `docs/architecture/cross-system-report.md`;
integration doc: `docs/architecture/polygrow-and-rustenwer-integration.md`.

- **Polygrow is the central intelligence-production platform.** It owns shared
  infrastructure (orchestration, compute job lifecycle, Modal integration and
  credentials, tenant identity/authorization, budgets/credits/usage, general
  artifact infrastructure, Developer API, user-facing experience). Its
  Intelligence Compute Platform (Spec B) is plan-only as of 2026-11-19: no
  Modal code, no model registry, no training code, no Developer API in
  Polygrow yet.
- **Syrius is the specialized reinforcement-learning system** (environments,
  simulations, rollouts, policies, RL algorithms, training, evaluation). It
  keeps its RL domain (`rl.py`, tool registry, independent evaluation,
  manifest + validated policy package) and exposes it as stable domain
  operations Polygrow can orchestrate. It does not become a second
  general-purpose compute platform.
- **Modal is the only initial remote compute provider.** There is no
  remote-provider code in this repo today; the only trace is the
  `"provision_gpu_instance"` string in the `PAID_COMPUTE_ACTIONS` boundary,
  explicitly not implemented. Do not introduce RunPod, AWS, Kubernetes, or
  any other remote provider. Local CPU execution stays for local dev,
  lightweight processing, and tests.
- **Rustenwer is the complementary specialized system** (model engineering:
  model creation, adaptation, training, fine-tuning, optimization,
  evaluation, packaging). The two repos collaborate through explicit
  artifacts, APIs, or orchestration contracts — never by importing each
  other's internals, and neither depends on the other to operate.
- **Integration is additive and compatibility-first.** Adapters around
  existing behavior; new paths behind flags; old paths deprecated only after
  equivalence on real workloads. No breaking API/schema changes without
  migration and rollback. No Modal credentials in this repo, ever. A
  completed compute job is not an improved policy — independent evaluation
  stays the arbiter of quality.

## What is not built yet

Auth is not built. The Phase 7 hardening pass is done: the API now
has list endpoints for experiments/episodes/evaluations, a
training-history endpoint (persisted metrics.csv), artifact download,
and a traversal guard on storage paths; the Experiment Studio chart
plots persisted history + live points and the Deliverables tab
downloads the package zip. Still missing: training resume,
logs/resource usage, scenario comparison, a department/tasks model.
See `IMPLEMENTATION_STATUS.md` at the repo root for the honest
per-item state.

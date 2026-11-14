# Syrius

![Syrius logo — the star Sirius](docs/assets/syrius-logo.webp)

**Syrius is an open-source RL Engineering Factory**: departments, studios
and reproducible reinforcement-learning pipelines — built in the open, one
phase at a time.

> **Status: Phases 1–6 — Backend vertical slice (v0.1) + Phase 5 Four
> Studios.** The monorepo skeleton, the API health service, the worker
> heartbeat CLI, PostgreSQL + Alembic, the web SPA shell and CI are in
> place, and the backend now runs a real CartPole slice end to end:
> project → spec → environment → PPO training (20,000 steps) →
> independent evaluation → policy export, all through the job queue and
> the worker. **Measured: baseline mean 23.35, PPO evaluation mean
> 498.70/500, success rate 0.95 (19/20).** The Four Studios are built
> on top of that API: Project Studio (spec, departments from the tool
> registry, approvals, audit timeline), Environment Studio (canvas
> CartPole playback from recorded episode traces), Experiment Studio
> (live SSE progress + ECharts curves, checkpoints, comparison) and
> Evaluation Studio (report.md/json, baseline/run comparison) plus a
> Deliverables tab (policy manifest + export). Where the backend lacks
> a list endpoint or a feature (training resume, artifact download,
> logs), the UI says so honestly instead of faking it. Hardening
> (Phase 7) is not built yet. See
> [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for the honest
> per-item state and
> [docs/evidence/cartpole-slice-2026-11-14.md](docs/evidence/cartpole-slice-2026-11-14.md)
> for the measured run.

## Quickstart

Prerequisites: Node.js 24 + pnpm 12, Python 3.12 + uv 0.12, Docker.

```sh
git clone https://github.com/SRogDev/Syrius.git
cd Syrius
make install     # uv sync + pnpm install
cp .env.example .env
make up          # PostgreSQL via Docker Compose
make migrate     # Alembic: creates worker_registrations
make dev-api     # FastAPI on http://localhost:8000
make dev-web     # TanStack Start SPA on http://localhost:3000
```

Open [http://localhost:3000](http://localhost:3000): the home page shows
the live API health panel. If PostgreSQL is down, the API honestly
reports `status: degraded` and `db: unavailable`.

Verify everything:

```sh
make check       # ruff + Biome lint, pytest, web production build
```

Run the real CartPole acceptance slice (no Docker needed — SQLite
local DB, real worker CLI, PPO 20,000 steps on CPU, ~2 minutes):

```sh
make slice
```

It writes its measured report to
`var/results/cartpole-slice-<timestamp>/report.md` (gitignored
runtime dir); the committed evidence copy lives in `docs/evidence/`.

Full install steps live in the docs: `docs/src/content/docs/getting-started.md`
(or run `pnpm --filter syrius-docs dev`).

## Stack

| Layer    | Technology                                                                                                  |
| -------- | ----------------------------------------------------------------------------------------------------------- |
| Web      | TanStack Start 1.169.5 (SPA mode), React 19, TanStack Router/Query, Tailwind v4, TypeScript 6 strict, Biome |
| API      | Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, uvicorn, Gymnasium, Stable-Baselines3, LangGraph       |
| Worker   | Python 3.12, SQLAlchemy, Gymnasium, Stable-Baselines3                                                       |
| Database | PostgreSQL 16 (self-managed Docker Compose; no Supabase) — SQLite for local dev/tests                       |
| Docs     | Astro Starlight                                                                                             |
| CI       | GitHub Actions (ruff, Biome, pytest, web + docs builds)                                                     |

Exact pinned versions — verified against the live registries on
2026-11-14 — are recorded in
[`docs/architecture/versions.md`](docs/src/content/docs/architecture/versions.md).

RL libraries (Gymnasium 1.4.0, Stable-Baselines3 2.9.2, torch 2.15.0+cpu,
LangGraph 0.6.8) are installed since Phases 1–6. Torch is the CPU build
from the PyTorch CPU index — the per-package index source only applies
when torch is a direct dependency (verified the hard way). Pinned
versions live in `docs/architecture/versions.md`.

## Structure

```text
syrius/
├── apps/
│   ├── web/        TanStack Start SPA (/, /projects, /projects/$projectId with
│   │               the Four Studios, /experiments/$id, /episodes/$id,
│   │               /evaluations/$id)
│   ├── api/        FastAPI — health + full /api/v1/ routes + Alembic
│   └── worker/     status / heartbeat CLI + run job loop
├── packages/
│   └── api-client/ OpenAPI-generated TypeScript types
├── scripts/        CartPole acceptance run + API client generator
├── docs/           Astro Starlight documentation (+ evidence/)
├── infrastructure/ Dockerfiles + docker-compose.yml
├── tests/          Reserved for future end-to-end tests
├── Makefile        install / dev / test / lint / migrate / up / down / slice
└── IMPLEMENTATION_STATUS.md   Honest per-item phase tracking
```

## Design

HUD / Sci-Fi FUI style (design authority: `ui-ux-pro-max` only), adapted
to the Syrius palette — Background `#111318`, Surface `#20242C`,
Platinum `#BFC5CE`, Highlight `#E7EBF2` — with Exo + Roboto Mono font
stacks using local/system fallbacks. Google Fonts is never fetched at
build time. Dark industrial, precise, dense but readable; no neon, no
generic SaaS dashboard look.

## What Phases 1–6 do — and do not do

**Do:** everything in Phase 0, plus the full backend slice: projects,
RL problem specs (Architect), Gymnasium environments (CartPole-v1
validated), a Postgres-backed job queue with a real worker loop, PPO
training via SB3 (never inside a request handler), SSE live progress,
independent evaluation with success = full 500-step episodes, policy
packaging/export with a reproducibility manifest and independent
package validation, 71 department tool definitions, LangGraph training
workflows, and OpenAPI-generated TS client types. Measured on
2026-11-14: random baseline mean 23.35; PPO (20,000 steps, seed 42)
evaluation mean 498.70/500, success 0.95 (19/20); export validated
independently (5 episodes, seed 1000: mean 492.80, success 0.80).

**Do not do:** auth, paid compute, production deploys, or hardening
(Phase 7). The Studios do not fake what the backend lacks: there are
no list endpoints for experiments, episodes or evaluations (objects
open by id), no training resume, no artifact download, and no
training-history endpoint, so the reward curve plots live-observed
points only. Nothing is mocked to look finished: tools and routes
that cannot run for real say `not_implemented` with the reason.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the working agreement in
[AGENTS.md](AGENTS.md). One reviewable unit per commit, conventional
commits, TDD with RED→GREEN evidence.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Roger Modesto Oria González.

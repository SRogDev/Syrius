# AGENTS.md — Syrius working agreement

How to work in this repo. Read this before writing code.

## Project

Syrius is an open-source **RL Engineering Factory**: departments, studios
and reproducible reinforcement-learning pipelines. Built in phases
(0–7); see `IMPLEMENTATION_STATUS.md` for what each phase contains and
its honest state.

## Stack (Phase 0, pinned — see `docs/architecture/versions.md`)

- **Web:** TanStack Start 1.169.5 in SPA mode, React 19, Tailwind v4,
  TypeScript 6 strict, Biome. pnpm workspaces.
- **API:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic,
  PostgreSQL 16 (self-managed, no Supabase). uv workspace.
- **Worker:** Python 3.12, SQLAlchemy, PostgreSQL.
- **Docs:** Astro Starlight.
- **RL (Phases 1–6, installed):** Gymnasium 1.4.0 / Stable-Baselines3
  2.9.2 / torch 2.15.0+cpu / LangGraph 0.6.8.

## Discipline (mandatory)

- **gentle-ai:** ODD routing, TDD RED→GREEN evidence, RDD self-review
  (`git diff`) before delivery.
- **Karpathy guidelines:** simplicity first, minimum code, no speculative
  abstractions, surgical changes.
- **Conventional commits**, one reviewable unit per commit.
- **Ruff** (Python) + **Biome** (TS) + **strict TS**, zero errors before
  delivery. `make check` runs lint + tests + web build.

## Design

- Design authority: **ui-ux-pro-max only** (HUD / Sci-Fi FUI adapted to
  the Syrius palette: Background `#111318`, Surface `#20242C`,
  Platinum `#BFC5CE`, Highlight `#E7EBF2`). Never load `impeccable`.
- Fonts: Exo + Roboto Mono with local/system fallbacks. **Never fetch
  Google Fonts at build time** (blocked by the sandbox egress proxy).

## Hard rules

- No secrets in the repo (`.env` gitignored; `.env.example` only).
- No fake training, metrics or health checks. A down database is
  `degraded` / `unavailable`, never green. No mocks in acceptance paths;
  stubs say "not yet implemented".
- No speculative scope: build only the current phase. Record deferred
  items in `IMPLEMENTATION_STATUS.md`.
- Every significant change updates the README in the same PR.
- GitHub pace: human pace, direct pushes to `main` for small changes,
  PRs for big changes. Never the burst pattern (no mass API-driven
  repo/PR creation, no auto-merge scripts).

## Layout

```text
apps/web       TanStack Start SPA
apps/api       FastAPI + Alembic (+ syrius_api: models, rl, jobs, executor,
               tools, capabilities, workflows, storage, routers)
apps/worker    Worker CLI (status / heartbeat / run job loop)
packages/api-client  OpenAPI-generated TypeScript types (scripts/gen_api_client.py)
scripts/       Acceptance run (run_cartpole_slice.py) + client generator
docs/          Astro Starlight (src/content/docs) + evidence/
infrastructure/docker + docker-compose.yml
tests/         Reserved for future end-to-end tests
```

## Gotchas (verified on this VM)

- `uv sync` + hatchling fails in this sandbox (isolated build env cannot
  fetch `hatchling.build_meta`); the workspace uses `uv_build` instead.
- Docker daemon cannot start in this sandbox (`dockerd` fails on
  iptables: permission denied even under sudo). PostgreSQL live checks
  are Blocked until a machine with Docker runs `make up`. Local dev
  and tests use SQLite (`DATABASE_URL=sqlite:///...`); the same schema
  is exercised via `Base.metadata.create_all`.
- `pkill -f "<pattern>"` matches your own shell when the pattern appears
  in your command line — kill test servers by PID, never by pattern.
- Torch CPU index: a per-package `tool.uv.sources` index only applies
  when the package is a DIRECT dependency — pin `torch` in
  `apps/api/pyproject.toml` or uv resolves the CUDA build from PyPI.
- `pnpm exec biome check .` also formats Markdown and JSON — new
  `.md`/`.json` files must be Biome-clean (`biome check --write`).
- Worker `heartbeat` raw SQL must insert `created_at`/`updated_at`
  explicitly: the ORM model has Python-side defaults only, so raw
  SQL against a `create_all` (SQLite) schema hits NOT NULL otherwise.
- Phase 0 worker tests assumed no database exists; CI runs a Postgres
  service, so they force an unreachable `DATABASE_URL` (closed port)
  instead of relying on the environment.

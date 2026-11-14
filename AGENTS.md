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
- **RL (NOT in Phase 0):** Gymnasium 1.4.0 / Stable-Baselines3 2.9.2 —
  verified compatible with Python 3.12, installed in Phase 1 only.

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
apps/api       FastAPI + Alembic
apps/worker    Worker CLI
docs/          Astro Starlight (src/content/docs)
infrastructure/docker + docker-compose.yml
tests/         Reserved for future end-to-end tests
```

There is no `packages/` directory yet: no shared package contains real
code. It appears when the first real shared code does (planned: OpenAPI-
generated API client types, Phase 1+).

## Gotchas (verified on this VM)

- `uv sync` + hatchling fails in this sandbox (isolated build env cannot
  fetch `hatchling.build_meta`); the workspace uses `uv_build` instead.
- Docker daemon cannot start in this sandbox (`dockerd` fails on
  iptables: permission denied even under sudo). PostgreSQL live checks
  are Blocked until a machine with Docker runs `make up`.
- `pkill -f "<pattern>"` matches your own shell when the pattern appears
  in your command line — kill test servers by PID, never by pattern.

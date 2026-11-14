# Syrius

![Syrius logo — the star Sirius](docs/assets/syrius-logo.webp)

**Syrius is an open-source RL Engineering Factory**: departments, studios
and reproducible reinforcement-learning pipelines — built in the open, one
phase at a time.

> **Status: Phase 0 — Repository Foundation (v0.1).** The monorepo
> skeleton, the API health service, the worker heartbeat CLI, PostgreSQL
> - Alembic, the web SPA shell and CI are in place and tested. **No RL
> training, projects, runs, departments or studios exist yet** — those are
> Phases 1–7. See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
> for the honest per-item state.

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

Full install steps live in the docs: `docs/src/content/docs/getting-started.md`
(or run `pnpm --filter syrius-docs dev`).

## Stack

| Layer    | Technology                                                                                                  |
| -------- | ----------------------------------------------------------------------------------------------------------- |
| Web      | TanStack Start 1.169.5 (SPA mode), React 19, TanStack Router/Query, Tailwind v4, TypeScript 6 strict, Biome |
| API      | Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, uvicorn                                                |
| Worker   | Python 3.12, SQLAlchemy                                                                                     |
| Database | PostgreSQL 16 (self-managed Docker Compose; no Supabase)                                                    |
| Docs     | Astro Starlight                                                                                             |
| CI       | GitHub Actions (ruff, Biome, pytest, web + docs builds)                                                     |

Exact pinned versions — verified against the live registries on
2026-11-14 — are recorded in
[`docs/architecture/versions.md`](docs/src/content/docs/architecture/versions.md).

RL libraries (Gymnasium 1.4.0, Stable-Baselines3 2.9.2) were verified
compatible with Python 3.12 but are **not installed** in Phase 0: no RL
code exists yet. They land with Phase 1.

## Structure

```text
syrius/
├── apps/
│   ├── web/        TanStack Start SPA (/, /projects, /projects/$projectId)
│   ├── api/        FastAPI — GET /health, GET /api/v1/health + Alembic
│   └── worker/     status / heartbeat CLI (DB-backed registration)
├── docs/           Astro Starlight documentation
├── infrastructure/ Dockerfiles + docker-compose.yml
├── tests/          Reserved for future end-to-end tests
├── Makefile        install / dev / test / lint / migrate / up / down
└── IMPLEMENTATION_STATUS.md   Honest per-item phase tracking
```

There is no `packages/` directory in Phase 0: no shared package contains
real code yet. API client types generated from the API's OpenAPI schema
will create it when Phase 1 adds real routes.

## Design

HUD / Sci-Fi FUI style (design authority: `ui-ux-pro-max` only), adapted
to the Syrius palette — Background `#111318`, Surface `#20242C`,
Platinum `#BFC5CE`, Highlight `#E7EBF2` — with Exo + Roboto Mono font
stacks using local/system fallbacks. Google Fonts is never fetched at
build time. Dark industrial, precise, dense but readable; no neon, no
generic SaaS dashboard look.

## What Phase 0 does — and does not do

**Does:** monorepo skeleton; API health with real DB reachability;
worker registration + heartbeat; PostgreSQL + Alembic baseline; web SPA
shell with live health panel; Starlight docs; CI.

**Does not do:** projects, runs, environments, training, departments,
studios, auth, BYOK, payments, deployments. Nothing is mocked to look
finished: skeleton pages say "not yet implemented" where that is true.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the working agreement in
[AGENTS.md](AGENTS.md). One reviewable unit per commit, conventional
commits, TDD with RED→GREEN evidence.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Roger Modesto Oria González.

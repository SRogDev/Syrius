---

title: Development
description: How to develop Syrius in Phase 0 — workflow, discipline, commands.
---

## Workflow

Syrius follows **gentle-ai discipline** on all coding work:

- **ODD routing** — small tasks inline, large/architectural work planned
  first (spec before code).
- **TDD** — write the failing test first (RED), implement (GREEN), then
  refactor while green. Report RED→GREEN evidence, not just "tests pass".
- **RDD self-review** — `git diff` review before delivery: risk,
  resilience, readability, reliability.
- **Karpathy guidelines** — simplicity first, minimum code, no speculative
  abstractions, surgical changes.

## Commands

```sh
make install   # uv sync + pnpm install
make up        # start PostgreSQL
make migrate   # alembic upgrade head
make dev-api   # FastAPI on :8000
make dev-web   # web SPA on :3000
make test      # pytest (api + worker) + web production build
make lint      # ruff + Biome
make check     # lint + test
```

## Conventions

- **Conventional commits**, one reviewable unit per commit
  (`feat:`, `fix:`, `docs:`, `chore:`, `test:`).
- **Strict TypeScript** (`strict: true`, no `any` without justification),
  **Ruff** for Python, **Biome** for TypeScript.
- **No secrets in the repo.** `.env` is gitignored; see `.env.example`.
- **No fake training or metrics.** No mocks in acceptance paths — label
  stubs "not yet implemented".
- **Design authority is `ui-ux-pro-max` only** (HUD / Sci-Fi FUI style,
  Syrius palette). Never load the abandoned `impeccable` skill.
- **Fonts are local/system fallbacks only** (Exo + Roboto Mono stacks):
  Google Fonts is not fetched at build time.

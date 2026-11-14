# Contributing to Syrius

Syrius is open source (MIT). Contributions are welcome — please read this
first.

## Workflow

1. Fork the repo and create a branch from `main`.
2. Follow the development discipline in `docs/src/content/docs/development.md`:
   gentle-ai (ODD routing, TDD RED→GREEN, RDD self-review) and the
   Karpathy guidelines (simplicity first, surgical changes).
3. Run `make check` before opening a PR (Ruff + Biome + pytest + web build).
4. One reviewable unit per PR; conventional commit messages
   (`feat:`, `fix:`, `docs:`, `chore:`, `test:`).

## Rules that are not negotiable

- **No secrets in the repo.** `.env` is gitignored; see `.env.example`.
- **No fake training, metrics or health.** If a component is down, report
  it as down. No mocks in acceptance paths — label stubs "not yet
  implemented".
- **No speculative scope.** Build only what the current phase's plan asks
  for; record deferred items in `IMPLEMENTATION_STATUS.md`.
- **Design authority is `ui-ux-pro-max` only** for frontend/UI work.
- **English** for README, docs and code comments.

## Reporting bugs

Open an issue with: what you ran (exact command), what you expected, what
happened (exact output), and your toolchain versions (`node --version`,
`uv --version`, `docker --version`).

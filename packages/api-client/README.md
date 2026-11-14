# syrius-api-client

Generated TypeScript types for the Syrius API, produced from the live
OpenAPI schema — not hand-written.

```sh
uv run --project apps/api python scripts/gen_api_client.py
```

`src/types.ts` carries every schema the API publishes plus an
`ApiOperations` map (operation → method, path, response type). The
package is intentionally **not** a pnpm workspace member (no runtime
dependencies, no build step): the Phase 5 web app imports the types
by relative path.

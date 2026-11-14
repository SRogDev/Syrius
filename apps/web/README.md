# Syrius web

TanStack Start SPA (React 19, Tailwind v4) for the Syrius RL Engineering
Factory.

Phase 0 scope: routing shell + home and project placeholder pages wired
to the real API health endpoint. No business data exists yet — pages say
"not yet implemented" where that is true.

## Routes

| Route                  | Content                                                  |
| ---------------------- | -------------------------------------------------------- |
| `/`                    | Home: Syrius intro, live API health panel, Phase 0 scope |
| `/projects`            | Placeholder — projects arrive with Phase 1               |
| `/projects/$projectId` | Placeholder project detail                               |

## Run

```sh
pnpm --filter syrius-web dev   # :3000, proxies /api to the API on :8000
```

## Verify

```sh
pnpm --filter syrius-web build       # production build (SPA prerender)
pnpm --filter syrius-web typecheck   # tsc --noEmit (strict)
```

## Design

HUD / Sci-Fi FUI style (ui-ux-pro-max design authority) adapted to the
Syrius palette: Background `#111318`, Surface `#20242C`, Platinum
`#BFC5CE`, Highlight `#E7EBF2`. Fonts are Exo + Roboto Mono with
local/system fallbacks — Google Fonts is never fetched at build time.

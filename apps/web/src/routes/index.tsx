import { createFileRoute, Link } from '@tanstack/react-router';
import ApiHealth from '../components/ApiHealth';
import { Button } from '../components/ui/button';

export const Route = createFileRoute('/')({ component: Home });

const BUILT = [
  'Monorepo skeleton (pnpm workspaces + uv workspace)',
  'FastAPI service with real /health and /api/v1/health',
  'Worker registration + heartbeat CLI',
  'PostgreSQL via Docker Compose + Alembic baseline migration',
  'CI: ruff, Biome, pytest, web build, docs build',
  'Backend vertical slice: project → spec → CartPole env → PPO training → evaluation → policy export (measured 2026-11-14: eval mean 498.70/500, success 0.95)',
  'Four Studios: Project, Environment (canvas CartPole playback), Experiment (live SSE + ECharts), Evaluation (report + comparisons), plus Deliverables/export',
];

const NOT_BUILT = [
  'Auth, teams, billing — not in v0.1 scope',
  'List endpoints for experiments, episodes and evaluations (Studios open objects by id; see IMPLEMENTATION_STATUS.md Phase 5)',
  'Training resume, artifact download, training logs / resource usage — backend gaps, shown honestly in the UI',
  'Hardening (Phase 7)',
];

function Home() {
  return (
    <div className="space-y-8">
      <section className="hud-panel px-6 py-10 sm:px-10">
        <div className="flex flex-col items-start gap-6 sm:flex-row sm:items-center">
          <img
            src="/syrius-logo.webp"
            alt="Syrius logo — the star Sirius"
            className="h-24 w-24 shrink-0 object-contain"
          />
          <div>
            <p className="mb-2 font-mono text-xs uppercase tracking-[0.3em] text-platinum">
              RL Engineering Factory · v0.1
            </p>
            <h1 className="font-display text-4xl font-bold tracking-wide text-highlight sm:text-5xl">
              SYRIUS
            </h1>
            <p className="mt-3 max-w-2xl text-base leading-relaxed text-platinum">
              An open-source factory for reinforcement-learning engineering:
              departments, studios and reproducible RL pipelines — built in the
              open, one phase at a time.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/projects">
                <Button>View projects</Button>
              </Link>
              <a
                href="https://github.com/SRogDev/Syrius"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="outline">GitHub</Button>
              </a>
            </div>
          </div>
        </div>
      </section>

      <ApiHealth />

      <div className="grid gap-4 md:grid-cols-2">
        <section className="hud-panel p-5">
          <h2 className="mb-3 font-mono text-xs uppercase tracking-[0.25em] text-platinum">
            Built — Phases 0–6
          </h2>
          <ul className="space-y-2 text-sm text-highlight">
            {BUILT.map((item) => (
              <li key={item} className="flex gap-2">
                <span aria-hidden className="text-highlight">
                  ▸
                </span>
                {item}
              </li>
            ))}
          </ul>
        </section>
        <section className="hud-panel p-5">
          <h2 className="mb-3 font-mono text-xs uppercase tracking-[0.25em] text-platinum">
            Not yet implemented
          </h2>
          <ul className="space-y-2 text-sm text-platinum">
            {NOT_BUILT.map((item) => (
              <li key={item} className="flex gap-2">
                <span aria-hidden className="text-muted">
                  ▸
                </span>
                {item}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}

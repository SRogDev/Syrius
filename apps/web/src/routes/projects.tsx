import { createFileRoute, Link } from '@tanstack/react-router';

export const Route = createFileRoute('/projects')({
  component: Projects,
});

function Projects() {
  return (
    <div className="space-y-6">
      <header>
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-platinum">
          Factory floor
        </p>
        <h1 className="mt-1 font-display text-3xl font-bold tracking-wide text-highlight">
          PROJECTS
        </h1>
      </header>
      <section className="hud-panel p-6">
        <p className="text-base text-platinum">
          No projects exist yet. Projects arrive with Phase 1 — this page is a
          wired route shell, not mock data.
        </p>
        <p className="mt-4 font-mono text-sm text-muted">
          <Link
            to="/"
            className="cursor-pointer text-highlight underline-offset-4 hover:underline"
          >
            ← Back to home
          </Link>
        </p>
      </section>
    </div>
  );
}

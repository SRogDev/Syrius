import { createFileRoute, Link } from '@tanstack/react-router';

export const Route = createFileRoute('/projects/$projectId')({
  component: ProjectDetail,
});

function ProjectDetail() {
  const { projectId } = Route.useParams();
  return (
    <div className="space-y-6">
      <header>
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-platinum">
          Factory floor / Projects
        </p>
        <h1 className="mt-1 font-display text-3xl font-bold tracking-wide text-highlight">
          PROJECT {projectId}
        </h1>
      </header>
      <section className="hud-panel p-6">
        <p className="text-base text-platinum">
          Project detail is not yet implemented (Phase 1). The route is wired;
          there is no project data behind it.
        </p>
        <p className="mt-4 font-mono text-sm text-muted">
          <Link
            to="/projects"
            className="cursor-pointer text-highlight underline-offset-4 hover:underline"
          >
            ← Back to projects
          </Link>
        </p>
      </section>
    </div>
  );
}

import { useMutation, useQuery } from '@tanstack/react-query';
import { createFileRoute, Link } from '@tanstack/react-router';
import { useState } from 'react';
import {
  ApiErrorBox,
  Loading,
  Panel,
  SectionTitle,
  StatusBadge,
} from '#/components/ui';
import { Button } from '#/components/ui/button';
import { createProject, listProjects, type Project } from '#/lib/api';
import { queryClient } from '#/lib/query-client';

export const Route = createFileRoute('/projects')({
  component: Projects,
});

function Projects() {
  const projectsQuery = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  });
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () =>
      createProject({ name: name.trim(), description: description.trim() }),
    onSuccess: (project: Project) => {
      setName('');
      setDescription('');
      setFormError(null);
      void queryClient.invalidateQueries({ queryKey: ['projects'] });
      void queryClient.setQueryData(['project', project.id], project);
    },
    onError: (error: unknown) => {
      setFormError(
        error instanceof Error
          ? error.message
          : 'Could not create the project.',
      );
    },
  });

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

      <Panel>
        <SectionTitle>New project</SectionTitle>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (name.trim().length === 0) {
              setFormError('A project needs a name.');
              return;
            }
            create.mutate();
          }}
          className="flex flex-col gap-3 sm:flex-row sm:items-end"
        >
          <label className="flex-1">
            <span className="mb-1 block font-mono text-[11px] uppercase tracking-widest text-muted">
              Name
            </span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="CartPole balance"
              aria-label="Project name"
              className="h-10 w-full border border-line bg-bg px-3 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
            />
          </label>
          <label className="flex-1">
            <span className="mb-1 block font-mono text-[11px] uppercase tracking-widest text-muted">
              Objective
            </span>
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What should this project achieve?"
              aria-label="Project objective"
              className="h-10 w-full border border-line bg-bg px-3 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
            />
          </label>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? 'Creating…' : 'Create project'}
          </Button>
        </form>
        {formError ? (
          <p role="alert" className="mt-3 font-mono text-sm text-amber-300">
            {formError}
          </p>
        ) : null}
      </Panel>

      {projectsQuery.isPending ? (
        <Loading label="Loading projects…" />
      ) : projectsQuery.isError ? (
        <ApiErrorBox
          error={projectsQuery.error}
          onRetry={() => void projectsQuery.refetch()}
        />
      ) : projectsQuery.data.length === 0 ? (
        <Panel>
          <p className="text-base text-platinum">
            No projects exist yet. Create the first one above — it is stored by
            the real API, not a demo.
          </p>
        </Panel>
      ) : (
        <div className="grid gap-4 md:grid-cols-2" data-testid="project-list">
          {projectsQuery.data.map((project) => (
            <Link
              key={project.id}
              to="/projects/$projectId"
              params={{ projectId: project.id }}
              search={{ studio: 'overview' }}
              className="hud-panel block cursor-pointer p-5 transition-colors duration-150 hover:border-platinum"
            >
              <div className="flex items-start justify-between gap-3">
                <h2 className="font-display text-lg font-bold tracking-wide text-highlight">
                  {project.name}
                </h2>
                <StatusBadge status={project.status} />
              </div>
              {project.description ? (
                <p className="mt-2 text-sm text-platinum">
                  {project.description}
                </p>
              ) : null}
              <p className="mt-3 font-mono text-xs text-muted">{project.id}</p>
              <p className="mt-1 font-mono text-xs uppercase tracking-widest text-highlight">
                Open Project Studio →
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

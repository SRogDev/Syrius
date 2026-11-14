import { useQuery } from '@tanstack/react-query';
import { createFileRoute, Link } from '@tanstack/react-router';
import {
  BarChart3,
  FlaskConical,
  LayoutDashboard,
  type LucideIcon,
  Microscope,
  Package,
} from 'lucide-react';
import DeliverablesPanel from '#/components/studios/DeliverablesPanel';
import EnvironmentPanel from '#/components/studios/EnvironmentPanel';
import EvaluationPanel from '#/components/studios/EvaluationPanel';
import ExperimentsPanel from '#/components/studios/ExperimentsPanel';
import ProjectOverview from '#/components/studios/ProjectOverview';
import { ApiErrorBox, Loading } from '#/components/ui';
import { getProject } from '#/lib/api';
import { cn } from '#/lib/utils';

const STUDIOS = [
  'overview',
  'environment',
  'experiments',
  'evaluation',
  'deliverables',
] as const;
type StudioTab = (typeof STUDIOS)[number];

const LABELS: Record<StudioTab, string> = {
  overview: 'Project',
  environment: 'Environment',
  experiments: 'Experiments',
  evaluation: 'Evaluation',
  deliverables: 'Deliverables',
};

const ICONS: Record<StudioTab, LucideIcon> = {
  overview: LayoutDashboard,
  environment: Microscope,
  experiments: FlaskConical,
  evaluation: BarChart3,
  deliverables: Package,
};

export const Route = createFileRoute('/projects/$projectId')({
  validateSearch: (search: Record<string, unknown>): { studio: StudioTab } => {
    const studio = search.studio;
    return {
      studio: STUDIOS.includes(studio as StudioTab)
        ? (studio as StudioTab)
        : 'overview',
    };
  },
  component: ProjectDetail,
});

function ProjectDetail() {
  const { projectId } = Route.useParams();
  const { studio } = Route.useSearch();
  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId),
  });

  return (
    <div className="space-y-6">
      <header>
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-platinum">
          Factory floor / Projects / Project Studio
        </p>
        <h1 className="mt-1 font-display text-3xl font-bold tracking-wide text-highlight">
          {projectQuery.data
            ? projectQuery.data.name.toUpperCase()
            : `PROJECT ${projectId.slice(0, 8)}`}
        </h1>
      </header>

      {projectQuery.isPending ? (
        <Loading label="Loading project…" />
      ) : projectQuery.isError ? (
        <ApiErrorBox
          error={projectQuery.error}
          onRetry={() => void projectQuery.refetch()}
        />
      ) : projectQuery.data ? (
        <>
          <nav aria-label="Studios" className="flex flex-wrap gap-2">
            {STUDIOS.map((tab) => {
              const Icon = ICONS[tab];
              return (
                <Link
                  key={tab}
                  to="/projects/$projectId"
                  params={{ projectId }}
                  search={{ studio: tab }}
                  className={cn(
                    'flex h-9 cursor-pointer items-center gap-2 border px-4 font-mono text-xs uppercase tracking-widest transition-colors duration-150',
                    studio === tab
                      ? 'border-highlight bg-highlight text-bg'
                      : 'border-line text-platinum hover:border-platinum hover:text-highlight',
                  )}
                >
                  <Icon className="h-4 w-4" aria-hidden />
                  {LABELS[tab]} Studio
                </Link>
              );
            })}
          </nav>
          {studio === 'overview' ? (
            <ProjectOverview project={projectQuery.data} />
          ) : null}
          {studio === 'environment' ? (
            <EnvironmentPanel projectId={projectId} />
          ) : null}
          {studio === 'experiments' ? (
            <ExperimentsPanel projectId={projectId} />
          ) : null}
          {studio === 'evaluation' ? (
            <EvaluationPanel projectId={projectId} />
          ) : null}
          {studio === 'deliverables' ? (
            <DeliverablesPanel projectId={projectId} />
          ) : null}
        </>
      ) : null}
    </div>
  );
}

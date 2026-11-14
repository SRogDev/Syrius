import { useQuery } from '@tanstack/react-query';
import { createFileRoute, Link } from '@tanstack/react-router';
import EpisodePlayer from '#/components/EpisodePlayer';
import {
  ApiErrorBox,
  Loading,
  Panel,
  SectionTitle,
  Stat,
  StatusBadge,
} from '#/components/ui';
import { getEnvironment, getEpisode, getEpisodeTrace } from '#/lib/api';

/** Environment Studio — episode deep link. Loads the episode record
 * and its recorded trace, then renders the canvas player. */

export const Route = createFileRoute('/episodes/$episodeId')({
  component: EpisodeStudio,
});

function EpisodeStudio() {
  const { episodeId } = Route.useParams();
  const episode = useQuery({
    queryKey: ['episode', episodeId],
    queryFn: () => getEpisode(episodeId),
  });
  const trace = useQuery({
    queryKey: ['episode-trace', episodeId],
    queryFn: () => getEpisodeTrace(episodeId),
    enabled: episode.isSuccess,
  });
  const environment = useQuery({
    queryKey: ['environment', episode.data?.environment_id],
    queryFn: () => getEnvironment(episode.data?.environment_id ?? ''),
    enabled: Boolean(episode.data?.environment_id),
  });

  if (episode.isPending) return <Loading label="Loading episode…" />;
  if (episode.isError) return <ApiErrorBox error={episode.error} />;
  const ep = episode.data;

  return (
    <div className="space-y-6">
      <header>
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-platinum">
          Environment Studio
        </p>
        <h1 className="mt-1 font-display text-3xl font-bold tracking-wide text-highlight">
          EPISODE {ep.id.slice(0, 8).toUpperCase()}
        </h1>
        <p className="mt-2 font-mono text-xs text-muted">
          {ep.id} · seed {ep.seed} · environment{' '}
          {environment.data?.name ?? ep.environment_id.slice(0, 8)}
          {environment.data ? ` (${environment.data.gym_id})` : ''}
        </p>
      </header>

      <Panel>
        <SectionTitle>Episode record</SectionTitle>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm sm:grid-cols-4">
          <Stat label="Length" value={ep.length} />
          <Stat label="Total reward" value={ep.total_reward.toFixed(1)} />
          <Stat
            label="Success"
            value={ep.success === null ? '—' : ep.success ? 'yes' : 'no'}
            tone={ep.success ? 'ok' : 'warn'}
          />
          <Stat
            label="Trace artifact"
            value={
              ep.trace_artifact_id ? ep.trace_artifact_id.slice(0, 8) : 'none'
            }
          />
          {environment.data ? (
            <Stat
              label="Env status"
              value={<StatusBadge status={environment.data.status} />}
            />
          ) : null}
        </dl>
      </Panel>

      {trace.isPending ? (
        <Loading label="Loading episode trace…" />
      ) : trace.isError ? (
        <ApiErrorBox error={trace.error} onRetry={() => void trace.refetch()} />
      ) : (
        <>
          <p className="font-mono text-xs text-muted">
            Trace: {trace.data?.gym_id} · seed {trace.data?.seed} ·{' '}
            {trace.data?.steps.length} steps reconstructed from recorded
            observations.
          </p>
          <EpisodePlayer steps={trace.data?.steps ?? []} />
        </>
      )}

      <p className="font-mono text-xs text-muted">
        <Link
          to="/projects"
          className="cursor-pointer text-highlight underline-offset-4 hover:underline"
        >
          ← Back to projects
        </Link>
      </p>
    </div>
  );
}

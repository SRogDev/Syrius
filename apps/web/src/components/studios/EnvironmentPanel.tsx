import { useMutation, useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import EpisodePlayer from '#/components/EpisodePlayer';
import {
  ApiErrorBox,
  Loading,
  Panel,
  SectionTitle,
  Stat,
  StatusBadge,
} from '#/components/ui';
import {
  createEnvironment,
  type Environment,
  getEnvironment,
  getEpisode,
  getEpisodeTrace,
  listEnvironments,
  recordEpisode,
  validateEnvironment,
} from '#/lib/api';
import { queryClient } from '#/lib/query-client';

/** Environment Studio — the most important studio (plan §3).
 * Visual CartPole renderer built from RECORDED episode observations,
 * simulation controls, episode timeline, Agent + Environment
 * inspectors, episode analytics. Episodes are fetched by id
 * (GET /episodes/{id} + /trace) — the backend has no list-episodes
 * endpoint, so an episode is recorded on demand or pasted by id. */

export default function EnvironmentPanel({ projectId }: { projectId: string }) {
  const envs = useQuery({
    queryKey: ['environments'],
    queryFn: listEnvironments,
  });
  const projectEnvs = (envs.data ?? []).filter(
    (e: Environment) => e.project_id === projectId,
  );
  const [envId, setEnvId] = useState('');
  const [episodeId, setEpisodeId] = useState('');
  const [newEnvName, setNewEnvName] = useState('CartPole-v1');
  const [message, setMessage] = useState<string | null>(null);

  const selectedEnv = projectEnvs.find((e) => e.id === envId) ?? projectEnvs[0];
  const envDetail = useQuery({
    queryKey: ['environment', selectedEnv?.id],
    queryFn: () => getEnvironment(selectedEnv?.id ?? ''),
    enabled: Boolean(selectedEnv?.id),
  });
  const episode = useQuery({
    queryKey: ['episode', episodeId],
    queryFn: () => getEpisode(episodeId),
    enabled: episodeId.length > 0,
  });
  const trace = useQuery({
    queryKey: ['episode-trace', episodeId],
    queryFn: () => getEpisodeTrace(episodeId),
    enabled: episodeId.length > 0 && episode.isSuccess,
  });

  const createEnv = useMutation({
    mutationFn: () =>
      createEnvironment({
        project_id: projectId,
        name: newEnvName.trim() || 'CartPole-v1',
      }),
    onSuccess: (env) => {
      setEnvId(env.id);
      setMessage(`Environment created: ${env.id} (${env.gym_id})`);
      void queryClient.invalidateQueries({ queryKey: ['environments'] });
    },
    onError: (error: unknown) =>
      setMessage(
        error instanceof Error
          ? error.message
          : 'Could not create the environment.',
      ),
  });

  const validate = useMutation({
    mutationFn: () => validateEnvironment(selectedEnv?.gym_id ?? 'CartPole-v1'),
    onSuccess: (result) => {
      const out = result as {
        valid?: boolean;
        smoke_episode_length?: number;
        smoke_episode_reward?: number;
      };
      setMessage(
        `Validation: ${out.valid ? 'valid' : 'invalid'} — smoke episode length ${out.smoke_episode_length}, reward ${out.smoke_episode_reward}.`,
      );
    },
    onError: (error: unknown) =>
      setMessage(error instanceof Error ? error.message : 'Validation failed.'),
  });

  const record = useMutation({
    mutationFn: () => recordEpisode(selectedEnv?.id ?? '', 0),
    onSuccess: (result) => {
      setEpisodeId(result.episode_id);
      setMessage(
        `Episode recorded: ${result.episode_id} — length ${result.length}, reward ${result.reward} (random policy).`,
      );
      void queryClient.invalidateQueries({
        queryKey: ['episode', result.episode_id],
      });
    },
    onError: (error: unknown) =>
      setMessage(
        error instanceof Error ? error.message : 'Could not record an episode.',
      ),
  });

  const steps = trace.data?.steps ?? [];

  return (
    <div className="space-y-4">
      <Panel>
        <SectionTitle>Environment</SectionTitle>
        {envs.isPending ? (
          <Loading label="Loading environments…" />
        ) : envs.isError ? (
          <ApiErrorBox error={envs.error} />
        ) : projectEnvs.length === 0 ? (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createEnv.mutate();
            }}
            className="flex flex-col gap-3 sm:flex-row sm:items-end"
          >
            <label className="flex-1">
              <span className="mb-1 block font-mono text-[11px] uppercase tracking-widest text-muted">
                Environment name
              </span>
              <input
                value={newEnvName}
                onChange={(e) => setNewEnvName(e.target.value)}
                aria-label="Environment name"
                className="h-10 w-full border border-line bg-bg px-3 font-mono text-sm text-highlight focus:outline-2 focus:outline-highlight"
              />
            </label>
            <button
              type="submit"
              disabled={createEnv.isPending}
              className="h-10 cursor-pointer border border-highlight bg-highlight px-4 font-mono text-xs uppercase tracking-widest text-bg transition-colors duration-150 hover:bg-platinum disabled:opacity-50"
            >
              {createEnv.isPending
                ? 'Creating…'
                : 'Create CartPole environment'}
            </button>
          </form>
        ) : (
          <div className="space-y-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <label className="flex-1">
                <span className="mb-1 block font-mono text-[11px] uppercase tracking-widest text-muted">
                  Environment
                </span>
                <select
                  value={selectedEnv?.id ?? ''}
                  onChange={(e) => setEnvId(e.target.value)}
                  aria-label="Environment"
                  className="h-10 w-full cursor-pointer border border-line bg-bg px-3 font-mono text-sm text-highlight"
                >
                  {projectEnvs.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.name} — {e.gym_id} (v{e.version})
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                onClick={() => validate.mutate()}
                disabled={validate.isPending || !selectedEnv}
                className="h-10 cursor-pointer border border-line px-4 font-mono text-xs uppercase tracking-widest text-highlight transition-colors duration-150 hover:border-platinum disabled:opacity-50"
              >
                {validate.isPending ? 'Validating…' : 'Validate (check_env)'}
              </button>
            </div>
            {envDetail.data ? (
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm sm:grid-cols-4">
                <Stat label="Gym id" value={envDetail.data.gym_id} />
                <Stat
                  label="Status"
                  value={<StatusBadge status={envDetail.data.status} />}
                />
                <Stat label="Version" value={envDetail.data.version} />
                <Stat
                  label="Config"
                  value={JSON.stringify(envDetail.data.config)}
                />
              </dl>
            ) : null}
          </div>
        )}
        {message ? (
          <p className="mt-3 font-mono text-sm text-platinum">{message}</p>
        ) : null}
      </Panel>

      <Panel>
        <SectionTitle>Episode — select or record</SectionTitle>
        <p className="mb-3 text-sm text-platinum">
          The backend has no list-episodes endpoint: open an episode by id, or
          record a fresh one from the selected environment (random policy,
          stored as a trace artifact).
        </p>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex-1">
            <span className="mb-1 block font-mono text-[11px] uppercase tracking-widest text-muted">
              Episode id
            </span>
            <input
              value={episodeId}
              onChange={(e) => setEpisodeId(e.target.value.trim())}
              placeholder="episode id"
              aria-label="Episode id"
              className="h-10 w-full border border-line bg-bg px-3 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
            />
          </label>
          <button
            type="button"
            onClick={() => record.mutate()}
            disabled={record.isPending || !selectedEnv}
            className="h-10 cursor-pointer border border-highlight bg-highlight px-4 font-mono text-xs uppercase tracking-widest text-bg transition-colors duration-150 hover:bg-platinum disabled:opacity-50"
          >
            {record.isPending ? 'Recording…' : 'Record episode'}
          </button>
        </div>
        {episode.data ? (
          <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm sm:grid-cols-4">
            <Stat label="Length" value={episode.data.length} />
            <Stat
              label="Total reward"
              value={episode.data.total_reward.toFixed(1)}
            />
            <Stat
              label="Success"
              value={
                episode.data.success === null
                  ? '—'
                  : episode.data.success
                    ? 'yes'
                    : 'no'
              }
            />
            <Stat label="Seed" value={episode.data.seed} />
          </dl>
        ) : null}
        {episode.isError ? <ApiErrorBox error={episode.error} /> : null}
      </Panel>

      {episodeId.length > 0 ? (
        trace.isPending ? (
          <Loading label="Loading episode trace…" />
        ) : trace.isError ? (
          <ApiErrorBox
            error={trace.error}
            onRetry={() => void trace.refetch()}
          />
        ) : (
          <>
            <p className="font-mono text-xs text-muted">
              Trace: {trace.data?.gym_id} · seed {trace.data?.seed} ·{' '}
              {steps.length} steps loaded from the recorded artifact (the API
              returns the full trace in one response; the player renders it
              progressively, one timestep at a time).
            </p>
            <EpisodePlayer steps={steps} />
          </>
        )
      ) : (
        <Panel>
          <p className="text-sm text-platinum">
            No episode selected. Record one above to watch the cart balance the
            pole — the renderer reconstructs cart position and pole angle from
            the recorded observations.
          </p>
        </Panel>
      )}
    </div>
  );
}

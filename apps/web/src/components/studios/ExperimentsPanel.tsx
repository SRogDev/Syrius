import { useMutation, useQuery } from '@tanstack/react-query';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
import {
  ApiErrorBox,
  Loading,
  Panel,
  SectionTitle,
  StatusBadge,
} from '#/components/ui';
import {
  createExperiment,
  type Environment,
  getExperiment,
  listEnvironments,
} from '#/lib/api';
import { queryClient } from '#/lib/query-client';

/** Project Studio — Experiments tab. The backend has no
 * list-experiments endpoint, so experiments are created here or opened
 * by id; the full Experiment Studio lives at /experiments/$id. */

export default function ExperimentsPanel({ projectId }: { projectId: string }) {
  const envs = useQuery({
    queryKey: ['environments'],
    queryFn: listEnvironments,
  });
  const projectEnvs = (envs.data ?? []).filter(
    (e: Environment) => e.project_id === projectId,
  );
  const [envId, setEnvId] = useState('');
  const [name, setName] = useState('PPO CartPole');
  const [experimentId, setExperimentId] = useState('');
  const [message, setMessage] = useState<string | null>(null);

  const selectedEnvId = envId || projectEnvs[0]?.id || '';
  const experiment = useQuery({
    queryKey: ['experiment', experimentId],
    queryFn: () => getExperiment(experimentId),
    enabled: experimentId.length > 0,
  });

  const create = useMutation({
    mutationFn: () =>
      createExperiment({
        project_id: projectId,
        environment_id: selectedEnvId,
        name: name.trim() || 'PPO CartPole',
        algorithm: 'PPO',
        config: { env_id: 'CartPole-v1', algorithm: 'PPO' },
      }),
    onSuccess: (exp) => {
      setExperimentId(exp.id);
      setMessage(`Experiment created: ${exp.id}`);
      void queryClient.invalidateQueries({ queryKey: ['experiment', exp.id] });
    },
    onError: (error: unknown) =>
      setMessage(
        error instanceof Error
          ? error.message
          : 'Could not create the experiment.',
      ),
  });

  return (
    <div className="space-y-4">
      <Panel>
        <SectionTitle>New experiment</SectionTitle>
        {projectEnvs.length === 0 ? (
          <p className="text-sm text-platinum">
            Create an environment first (Environment Studio tab) — an experiment
            needs one.
          </p>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!selectedEnvId) {
                setMessage('Pick an environment first.');
                return;
              }
              create.mutate();
            }}
            className="flex flex-col gap-3 sm:flex-row sm:items-end"
          >
            <label className="flex-1">
              <span className="mb-1 block font-mono text-[11px] uppercase tracking-widest text-muted">
                Environment
              </span>
              <select
                value={selectedEnvId}
                onChange={(e) => setEnvId(e.target.value)}
                aria-label="Environment"
                className="h-10 w-full cursor-pointer border border-line bg-bg px-3 font-mono text-sm text-highlight"
              >
                {projectEnvs.map((env) => (
                  <option key={env.id} value={env.id}>
                    {env.name} — {env.gym_id}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex-1">
              <span className="mb-1 block font-mono text-[11px] uppercase tracking-widest text-muted">
                Name
              </span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                aria-label="Experiment name"
                className="h-10 w-full border border-line bg-bg px-3 font-mono text-sm text-highlight focus:outline-2 focus:outline-highlight"
              />
            </label>
            <button
              type="submit"
              disabled={create.isPending}
              className="h-10 cursor-pointer border border-highlight bg-highlight px-4 font-mono text-xs uppercase tracking-widest text-bg transition-colors duration-150 hover:bg-platinum disabled:opacity-50"
            >
              {create.isPending ? 'Creating…' : 'Create experiment (PPO)'}
            </button>
          </form>
        )}
        {message ? (
          <p className="mt-3 font-mono text-sm text-platinum">{message}</p>
        ) : null}
      </Panel>

      <Panel>
        <SectionTitle>Open experiment by id</SectionTitle>
        <label className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <span className="font-mono text-xs uppercase tracking-widest text-muted">
            Experiment id
          </span>
          <input
            value={experimentId}
            onChange={(e) => setExperimentId(e.target.value.trim())}
            placeholder="experiment id"
            aria-label="Experiment id"
            className="h-10 flex-1 border border-line bg-bg px-3 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
          />
        </label>
        {experiment.isPending && experimentId ? (
          <Loading label="Loading experiment…" />
        ) : null}
        {experiment.isError ? <ApiErrorBox error={experiment.error} /> : null}
        {experiment.data ? (
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <span className="font-display text-lg font-bold text-highlight">
              {experiment.data.name}
            </span>
            <StatusBadge status={experiment.data.status} />
            <span className="font-mono text-xs text-muted">
              {experiment.data.algorithm}
            </span>
            <Link
              to="/experiments/$experimentId"
              params={{ experimentId: experiment.data.id }}
              className="cursor-pointer font-mono text-xs uppercase tracking-widest text-highlight underline-offset-4 transition-colors duration-150 hover:underline"
            >
              Open Experiment Studio →
            </Link>
          </div>
        ) : null}
      </Panel>
    </div>
  );
}

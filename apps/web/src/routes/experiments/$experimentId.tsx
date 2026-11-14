import { useMutation, useQuery } from '@tanstack/react-query';
import { createFileRoute, Link } from '@tanstack/react-router';
import { useCallback, useState } from 'react';
import RewardChart from '#/components/RewardChart';
import {
  ApiErrorBox,
  Loading,
  NotImplemented,
  Panel,
  SectionTitle,
  Stat,
  StatusBadge,
} from '#/components/ui';
import {
  baselineExperiment,
  cancelJob,
  evaluateExperiment,
  getExperiment,
  getExperimentMetrics,
  listCheckpoints,
  runTool,
  type TrainingConfig,
  trainExperiment,
} from '#/lib/api';
import type { RewardPoint } from '#/lib/charts';
import { queryClient } from '#/lib/query-client';
import { useExperimentProgress } from '#/lib/useExperimentProgress';

/** Experiment Studio. Experiment detail, algorithm + training config
 * (editable; edits apply to the NEXT training run — the backend has no
 * update-experiment endpoint, so config is versioned per run),
 * hyperparameters, live training progress via SSE (with metrics polling
 * fallback), reward curves via ECharts, checkpoints, logs, experiment
 * comparison, train / baseline / evaluate / stop controls.
 * The browser never trains — training is always a queued job. */

const DEFAULT_CONFIG: TrainingConfig = {
  env_id: 'CartPole-v1',
  algorithm: 'PPO',
  seed: 42,
  total_timesteps: 20000,
  learning_rate: 0.0003,
  n_steps: 2048,
  batch_size: 64,
  n_epochs: 10,
  gamma: 0.99,
  gae_lambda: 0.95,
  clip_range: 0.2,
};

const CONFIG_FIELDS: Array<{
  key: keyof TrainingConfig;
  label: string;
  step?: string;
}> = [
  { key: 'total_timesteps', label: 'Total timesteps', step: '1000' },
  { key: 'learning_rate', label: 'Learning rate', step: '0.0001' },
  { key: 'n_steps', label: 'n_steps', step: '128' },
  { key: 'batch_size', label: 'Batch size', step: '32' },
  { key: 'n_epochs', label: 'n_epochs', step: '1' },
  { key: 'gamma', label: 'Gamma', step: '0.01' },
  { key: 'gae_lambda', label: 'GAE lambda', step: '0.01' },
  { key: 'clip_range', label: 'Clip range', step: '0.05' },
  { key: 'seed', label: 'Seed', step: '1' },
];

export const Route = createFileRoute('/experiments/$experimentId')({
  component: ExperimentStudio,
});

function ExperimentStudio() {
  const { experimentId } = Route.useParams();
  const experiment = useQuery({
    queryKey: ['experiment', experimentId],
    queryFn: () => getExperiment(experimentId),
  });
  const checkpoints = useQuery({
    queryKey: ['checkpoints', experimentId],
    queryFn: () => listCheckpoints(experimentId),
  });
  const metricsQuery = useQuery({
    queryKey: ['experiment-metrics', experimentId],
    queryFn: () => getExperimentMetrics(experimentId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'running' || status === 'queued' ? 5000 : false;
    },
  });

  const [config, setConfig] = useState<TrainingConfig | null>(null);
  const [points, setPoints] = useState<RewardPoint[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [compareId, setCompareId] = useState('');

  const onPoint = useCallback((step: number, reward: number) => {
    setPoints((prev) => {
      if (prev.length > 0 && prev[prev.length - 1]?.step === step) return prev;
      return [...prev, { step, reward }].slice(-500);
    });
  }, []);
  const live = useExperimentProgress(experimentId, onPoint);

  const effectiveConfig: TrainingConfig = {
    ...DEFAULT_CONFIG,
    ...((experiment.data?.config ?? {}) as TrainingConfig),
    ...(config ?? {}),
  };

  const train = useMutation({
    mutationFn: () => trainExperiment(experimentId, effectiveConfig),
    onSuccess: (result) => {
      setJobId(result.job_id);
      setMessage(
        `Training enqueued — job ${result.job_id}, training run ${result.training_run_id}. The worker runs it; this page only watches.`,
      );
      void queryClient.invalidateQueries({
        queryKey: ['experiment-metrics', experimentId],
      });
    },
    onError: (error: unknown) =>
      setMessage(
        error instanceof Error ? error.message : 'Could not enqueue training.',
      ),
  });
  const baseline = useMutation({
    mutationFn: () => baselineExperiment(experimentId, 20, 0),
    onSuccess: (result) => {
      setJobId(result.job_id);
      setMessage(
        `Baseline (random policy, 20 episodes) enqueued — job ${result.job_id}.`,
      );
    },
    onError: (error: unknown) =>
      setMessage(
        error instanceof Error
          ? error.message
          : 'Could not enqueue the baseline.',
      ),
  });
  const evaluate = useMutation({
    mutationFn: () => evaluateExperiment(experimentId, {}),
    onSuccess: (result) => {
      setMessage(
        `Evaluation enqueued — run ${result.evaluation_run_id}, job ${result.job_id}.`,
      );
    },
    onError: (error: unknown) =>
      setMessage(
        error instanceof Error
          ? error.message
          : 'Could not enqueue evaluation.',
      ),
  });
  const stop = useMutation({
    mutationFn: () => cancelJob(jobId ?? ''),
    onSuccess: (job) => setMessage(`Job ${job.id} → ${job.status}.`),
    onError: (error: unknown) =>
      setMessage(
        error instanceof Error ? error.message : 'Could not cancel the job.',
      ),
  });

  const compare = useQuery({
    queryKey: ['experiment-compare', experimentId, compareId],
    queryFn: () =>
      runTool<{
        a: { id: string; config: Record<string, unknown>; status: string };
        b: { id: string; config: Record<string, unknown>; status: string };
      }>('CompareExperiments', {
        experiment_id_a: experimentId,
        experiment_id_b: compareId,
      }),
    enabled: compareId.length > 0,
  });
  const compareMetrics = useQuery({
    queryKey: ['experiment-metrics', compareId],
    queryFn: () => getExperimentMetrics(compareId),
    enabled: compareId.length > 0,
  });

  const liveMetrics = live.metrics ?? metricsQuery.data;
  const liveReward = (
    liveMetrics?.metrics as Record<string, unknown> | undefined
  )?.last_mean_episode_reward;
  const chartPoints: RewardPoint[] =
    points.length > 0
      ? points
      : liveMetrics && typeof liveReward === 'number'
        ? [{ step: liveMetrics.current_step ?? 0, reward: liveReward }]
        : [];

  const otherMetrics = compareMetrics.data?.metrics as Record<string, unknown> | undefined;
  const otherReward = otherMetrics?.last_mean_episode_reward;

  if (experiment.isPending) return <Loading label="Loading experiment…" />;
  if (experiment.isError)
    return (
      <ApiErrorBox
        error={experiment.error}
        onRetry={() => void experiment.refetch()}
      />
    );
  const exp = experiment.data;

  return (
    <div className="space-y-6">
      <header>
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-platinum">
          Experiment Studio / {exp.project_id.slice(0, 8)}
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h1 className="font-display text-3xl font-bold tracking-wide text-highlight">
            {exp.name.toUpperCase()}
          </h1>
          <StatusBadge status={exp.status} />
        </div>
        <p className="mt-2 font-mono text-xs text-muted">
          {exp.id} · {exp.algorithm} · env {exp.environment_id.slice(0, 8)}
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <SectionTitle>
            Training config — editable, versioned per run
          </SectionTitle>
          <p className="mb-3 text-sm text-platinum">
            Edits apply to the next training run (the backend has no
            update-experiment endpoint). Each run records the config it actually
            used; the version below is the config version sent with the next
            run.
          </p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {CONFIG_FIELDS.map((field) => (
              <label key={field.key}>
                <span className="mb-1 block font-mono text-[11px] uppercase tracking-widest text-muted">
                  {field.label}
                </span>
                <input
                  type="number"
                  step={field.step}
                  value={String(effectiveConfig[field.key] ?? '')}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...(prev ?? {}),
                      [field.key]: Number(e.target.value),
                    }))
                  }
                  aria-label={field.label}
                  className="h-9 w-full border border-line bg-bg px-2 font-mono text-sm text-highlight focus:outline-2 focus:outline-highlight"
                />
              </label>
            ))}
          </div>
          <p className="mt-3 font-mono text-xs text-muted">
            Config version for next run: {(effectiveConfig.version ?? 1) + 1}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => train.mutate()}
              disabled={train.isPending}
              className="h-10 cursor-pointer border border-highlight bg-highlight px-4 font-mono text-xs uppercase tracking-widest text-bg transition-colors duration-150 hover:bg-platinum disabled:opacity-50"
            >
              {train.isPending ? 'Enqueueing…' : 'Train (enqueue job)'}
            </button>
            <button
              type="button"
              onClick={() => baseline.mutate()}
              disabled={baseline.isPending}
              className="h-10 cursor-pointer border border-line px-4 font-mono text-xs uppercase tracking-widest text-highlight transition-colors duration-150 hover:border-platinum disabled:opacity-50"
            >
              {baseline.isPending ? 'Enqueueing…' : 'Baseline (random)'}
            </button>
            <button
              type="button"
              onClick={() => evaluate.mutate()}
              disabled={evaluate.isPending}
              className="h-10 cursor-pointer border border-line px-4 font-mono text-xs uppercase tracking-widest text-highlight transition-colors duration-150 hover:border-platinum disabled:opacity-50"
            >
              {evaluate.isPending ? 'Enqueueing…' : 'Evaluate'}
            </button>
            <button
              type="button"
              onClick={() => stop.mutate()}
              disabled={stop.isPending || !jobId}
              title={
                jobId
                  ? `Cancel job ${jobId}`
                  : 'No job started from this page yet — stop needs a job id'
              }
              className="h-10 cursor-pointer border border-line px-4 font-mono text-xs uppercase tracking-widest text-highlight transition-colors duration-150 hover:border-platinum disabled:opacity-50"
            >
              Stop job
            </button>
          </div>
          <p className="mt-3 text-sm text-platinum">
            There is no resume in v0.1: stopping cancels the job, and
            re-training enqueues a fresh run. The job id from this page is{' '}
            <code className="font-mono text-highlight">
              {jobId ?? 'none yet'}
            </code>
            .
          </p>
          {message ? (
            <p className="mt-2 font-mono text-sm text-platinum">{message}</p>
          ) : null}
        </Panel>

        <Panel>
          <SectionTitle>Live training progress</SectionTitle>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm">
            <Stat label="Status" value={liveMetrics?.status ?? 'no_run'} />
            <Stat
              label="Step"
              value={`${liveMetrics?.current_step ?? 0} / ${liveMetrics?.total_timesteps ?? 0}`}
            />
            <Stat
              label="Last mean episode reward"
              value={
                typeof liveReward === 'number' ? liveReward.toFixed(2) : '—'
              }
            />
            <Stat
              label="Live feed"
              value={
                live.usingFallback
                  ? 'SSE unavailable — polling /metrics every 2 s'
                  : live.connected
                    ? 'SSE connected'
                    : 'connecting…'
              }
            />
          </dl>
          <div className="mt-4">
            <RewardChart
              points={chartPoints}
              title="Training reward — live points"
            />
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <SectionTitle>Checkpoints</SectionTitle>
          {checkpoints.isPending ? (
            <Loading label="Loading checkpoints…" />
          ) : checkpoints.isError ? (
            <ApiErrorBox error={checkpoints.error} />
          ) : checkpoints.data.length === 0 ? (
            <p className="text-sm text-platinum">
              No checkpoints yet — they appear after a training run saves one.
            </p>
          ) : (
            <ul className="space-y-2 font-mono text-sm">
              {checkpoints.data.map((c) => (
                <li key={c.id} className="flex justify-between gap-3">
                  <span className="text-highlight">step {c.step}</span>
                  <span className="text-muted">{c.created_at ?? ''}</span>
                  <span className="text-muted">
                    {c.artifact_id.slice(0, 8)}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-3 text-sm text-muted">
            Checkpoint contents (metrics.csv, model zip) live in artifact
            storage; the API exposes artifact metadata, not file bytes.
          </p>
        </Panel>
        <Panel>
          <SectionTitle>Experiment comparison</SectionTitle>
          <label className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <span className="font-mono text-xs uppercase tracking-widest text-muted">
              Compare with experiment id
            </span>
            <input
              value={compareId}
              onChange={(e) => setCompareId(e.target.value.trim())}
              placeholder="second experiment id"
              aria-label="Second experiment id to compare"
              className="h-10 flex-1 border border-line bg-bg px-3 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
            />
          </label>
          {compare.data ? (
            <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm">
              <Stat
                label="This experiment"
                value={`${compare.data.a.status} · ${JSON.stringify(compare.data.a.config)}`}
              />
              <Stat
                label="Other experiment"
                value={`${compare.data.b.status} · ${JSON.stringify(compare.data.b.config)}`}
              />
              <Stat
                label="This last mean reward"
                value={
                  typeof liveReward === 'number' ? liveReward.toFixed(2) : '—'
                }
              />
              <Stat
                label="Other last mean reward"
                value={typeof otherReward === 'number' ? otherReward.toFixed(2) : '—'}
              />
            </dl>
          ) : null}
          {compare.isError ? <ApiErrorBox error={compare.error} /> : null}
          <p className="mt-3 text-sm text-muted">
            Comparison is config + latest training metrics. Reward curves are
            not stored per run by the backend, so there is no historical curve
            to overlay.
          </p>
        </Panel>
      </div>

      <NotImplemented
        what="Training logs and resource usage"
        reason="The backend stores job logs and metrics rows but exposes no log-stream or resource-usage endpoint in v0.1 (job error/retry count are available via GET /jobs/{id})."
      />
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

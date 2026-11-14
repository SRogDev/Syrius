import { useMutation, useQuery } from '@tanstack/react-query';
import { createFileRoute, Link } from '@tanstack/react-router';
import { useState } from 'react';
import {
  ApiErrorBox,
  Loading,
  Panel,
  SectionTitle,
  Stat,
  StatusBadge,
} from '#/components/ui';
import { getEvaluation, getEvaluationReport, runTool } from '#/lib/api';

/** Evaluation Studio. Evaluation suites, benchmark results, policy
 * and scenario comparison, success rates, reward distributions,
 * robustness, failure analysis, constraint violations, regression
 * results, report rendering (report.md + report.json), approval
 * status. Training reward, evaluation reward, task success and
 * robustness/constraint metrics are labelled as different things —
 * they are not interchangeable. */

const fmt = (v: unknown, digits = 2): string =>
  typeof v === 'number' && Number.isFinite(v) ? v.toFixed(digits) : '—';

export const Route = createFileRoute('/evaluations/$evaluationId')({
  component: EvaluationStudio,
});

function EvaluationStudio() {
  const { evaluationId } = Route.useParams();
  const evaluation = useQuery({
    queryKey: ['evaluation', evaluationId],
    queryFn: () => getEvaluation(evaluationId),
  });
  const report = useQuery({
    queryKey: ['evaluation-report', evaluationId],
    queryFn: () => getEvaluationReport(evaluationId),
    enabled: evaluation.isSuccess,
  });

  const [baselineMean, setBaselineMean] = useState('23.35');
  const [compareA, setCompareA] = useState(evaluationId);
  const [compareB, setCompareB] = useState('');
  const [jobId, setJobId] = useState('');
  const [toolMessage, setToolMessage] = useState<string | null>(null);

  const compareBaseline = useMutation({
    mutationFn: () =>
      runTool<{
        baseline_mean_reward: number | null;
        evaluation_mean_reward: number | null;
        improvement: number | null;
      }>('CompareBaseline', {
        evaluation_run_id: evaluationId,
        baseline: { mean_reward: Number(baselineMean) },
      }),
    onSuccess: (r) =>
      setToolMessage(
        `Baseline mean ${fmt(r.baseline_mean_reward)} vs evaluation mean ${fmt(r.evaluation_mean_reward)} — improvement ${r.improvement === null ? '—' : fmt(r.improvement)}. (Training reward is NOT shown here: this compares independent evaluation reward against the random baseline.)`,
      ),
    onError: (error: unknown) =>
      setToolMessage(
        error instanceof Error ? error.message : 'Baseline comparison failed.',
      ),
  });

  const compareRuns = useMutation({
    mutationFn: () =>
      runTool<{
        a: { id: string; metrics: Record<string, unknown> };
        b: { id: string; metrics: Record<string, unknown> };
      }>('CompareEvaluationRuns', {
        evaluation_run_id_a: compareA.trim(),
        evaluation_run_id_b: compareB.trim(),
      }),
    onSuccess: (r) =>
      setToolMessage(
        `Run A mean ${fmt(r.a.metrics.mean_reward)} / success ${fmt(r.a.metrics.success_rate)} vs run B mean ${fmt(r.b.metrics.mean_reward)} / success ${fmt(r.b.metrics.success_rate)}.`,
      ),
    onError: (error: unknown) =>
      setToolMessage(
        error instanceof Error ? error.message : 'Run comparison failed.',
      ),
  });

  const inspectFailure = useMutation({
    mutationFn: () =>
      runTool<{
        job_id: string;
        status: string;
        error: string | null;
        logs: string[];
      }>('InspectEvaluationFailure', {
        job_id: jobId.trim(),
      }),
    onSuccess: (r) =>
      setToolMessage(
        `Job ${r.job_id}: status ${r.status}, error: ${r.error ?? 'none'}. Logs: ${r.logs.length > 0 ? r.logs.join(' | ') : 'none recorded'}.`,
      ),
    onError: (error: unknown) =>
      setToolMessage(
        error instanceof Error ? error.message : 'Failure inspection failed.',
      ),
  });

  if (evaluation.isPending) return <Loading label="Loading evaluation…" />;
  if (evaluation.isError) return <ApiErrorBox error={evaluation.error} />;
  const run = evaluation.data;
  const m = run.metrics as Record<string, unknown>;
  const detail = Array.isArray(m.episodes_detail)
    ? (m.episodes_detail as Array<{ length: number; reward: number }>)
    : [];
  const rewards = detail.map((d) => d.reward).sort((a, b) => a - b);

  return (
    <div className="space-y-6">
      <header>
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-platinum">
          Evaluation Studio
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h1 className="font-display text-3xl font-bold tracking-wide text-highlight">
            EVALUATION {run.id.slice(0, 8).toUpperCase()}
          </h1>
          <StatusBadge status={run.status} />
        </div>
        <p className="mt-2 font-mono text-xs text-muted">
          {run.id} · experiment {run.experiment_id.slice(0, 8)}
          {run.policy_id
            ? ` · policy ${run.policy_id.slice(0, 8)}`
            : ' · no policy attached'}
        </p>
      </header>

      <Panel>
        <SectionTitle>
          Benchmark results — independent evaluation, not training reward
        </SectionTitle>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm sm:grid-cols-4">
          <Stat label="Evaluation mean reward" value={fmt(m.mean_reward)} />
          <Stat label="Median reward" value={fmt(m.median_reward)} />
          <Stat label="Mean episode length" value={fmt(m.mean_length)} />
          <Stat label="Episodes" value={String(m.episodes ?? '—')} />
          <Stat
            label="Task success (500-step eps)"
            value={
              m.success_rate === undefined
                ? '—'
                : `${fmt(m.success_rate, 2)} (${m.successes ?? '?'} / ${m.episodes ?? '?'})`
            }
            tone={
              typeof m.success_rate === 'number' && m.success_rate >= 0.8
                ? 'ok'
                : 'warn'
            }
          />
          <Stat
            label="Min / max reward"
            value={
              rewards.length > 0
                ? `${fmt(rewards[0], 1)} / ${fmt(rewards[rewards.length - 1], 1)}`
                : '—'
            }
          />
          <Stat
            label="Constraint violations"
            value={String(m.constraint_violations ?? '—')}
            tone={Number(m.constraint_violations ?? 0) > 0 ? 'warn' : 'ok'}
          />
          <Stat
            label="Seed / deterministic"
            value={`${String(m.seed ?? '—')} / ${String(m.deterministic ?? '—')}`}
          />
        </dl>
        <p className="mt-3 text-sm text-platinum">
          Read these as four different things:{' '}
          <strong className="text-highlight">training reward</strong> is the
          rolling mean during training (lower, and not shown here);{' '}
          <strong className="text-highlight">evaluation reward</strong> is the
          mean above, measured on a fresh deterministic run;{' '}
          <strong className="text-highlight">task success</strong> is the share
          of full 500-step episodes (the actual goal);{' '}
          <strong className="text-highlight">robustness / constraints</strong>{' '}
          is the violations count — zero here means no constraint was broken
          across the evaluated episodes.
        </p>
      </Panel>

      {rewards.length > 0 ? (
        <Panel>
          <SectionTitle>
            Reward distribution (per-episode evaluation rewards)
          </SectionTitle>
          <p className="font-mono text-xs text-muted">
            {rewards.map((r) => r.toFixed(0)).join(', ')}
          </p>
          <p className="mt-2 text-sm text-muted">
            {rewards.filter((r) => r >= 500).length} of {rewards.length}{' '}
            episodes reached the full 500 steps.
          </p>
        </Panel>
      ) : (
        <Panel>
          <SectionTitle>Reward distribution</SectionTitle>
          <p className="text-sm text-platinum">
            No per-episode detail in this run's metrics — only aggregates were
            stored. Distribution needs the episodes_detail array the evaluator
            writes.
          </p>
        </Panel>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <SectionTitle>Policy comparison — baseline vs this run</SectionTitle>
          <label className="flex items-center gap-2 font-mono text-xs text-platinum">
            Random baseline mean reward
            <input
              type="number"
              step="0.01"
              value={baselineMean}
              onChange={(e) => setBaselineMean(e.target.value)}
              aria-label="Random baseline mean reward"
              className="h-9 w-32 border border-line bg-bg px-2 font-mono text-sm text-highlight focus:outline-2 focus:outline-highlight"
            />
          </label>
          <button
            type="button"
            onClick={() => compareBaseline.mutate()}
            disabled={compareBaseline.isPending}
            className="mt-3 h-9 cursor-pointer border border-line px-4 font-mono text-xs uppercase tracking-widest text-highlight transition-colors duration-150 hover:border-platinum disabled:opacity-50"
          >
            Compare with baseline
          </button>
          <div className="mt-4 space-y-3">
            <label className="flex items-center gap-2 font-mono text-xs text-platinum">
              Run A
              <input
                value={compareA}
                onChange={(e) => setCompareA(e.target.value)}
                aria-label="First evaluation run id"
                className="h-9 flex-1 border border-line bg-bg px-2 font-mono text-sm text-highlight focus:outline-2 focus:outline-highlight"
              />
            </label>
            <label className="flex items-center gap-2 font-mono text-xs text-platinum">
              Run B
              <input
                value={compareB}
                onChange={(e) => setCompareB(e.target.value)}
                placeholder="second run id"
                aria-label="Second evaluation run id"
                className="h-9 flex-1 border border-line bg-bg px-2 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
              />
            </label>
            <button
              type="button"
              onClick={() => compareRuns.mutate()}
              disabled={compareRuns.isPending || compareB.trim().length === 0}
              className="h-9 cursor-pointer border border-line px-4 font-mono text-xs uppercase tracking-widest text-highlight transition-colors duration-150 hover:border-platinum disabled:opacity-50"
            >
              Compare two runs
            </button>
          </div>
          {toolMessage ? (
            <p className="mt-3 font-mono text-sm text-platinum">
              {toolMessage}
            </p>
          ) : null}
          <p className="mt-3 text-sm text-muted">
            Scenario comparison is not a separate API surface in v0.1 —
            scenarios share the environment config; compare runs that used
            different seeds or configs instead. Regression results likewise come
            from comparing runs over time, not from a regression endpoint.
          </p>
        </Panel>

        <Panel>
          <SectionTitle>Failure analysis + approval status</SectionTitle>
          <label className="flex items-center gap-2 font-mono text-xs text-platinum">
            Job id to inspect
            <input
              value={jobId}
              onChange={(e) => setJobId(e.target.value.trim())}
              placeholder="job id (from the evaluate response)"
              aria-label="Job id to inspect"
              className="h-9 flex-1 border border-line bg-bg px-2 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
            />
          </label>
          <button
            type="button"
            onClick={() => inspectFailure.mutate()}
            disabled={inspectFailure.isPending || jobId.trim().length === 0}
            className="mt-3 h-9 cursor-pointer border border-line px-4 font-mono text-xs uppercase tracking-widest text-highlight transition-colors duration-150 hover:border-platinum disabled:opacity-50"
          >
            Inspect failure
          </button>
          <p className="mt-4 text-sm text-platinum">
            Approval status:{' '}
            <strong className="text-highlight">unpublished</strong>. Publishing
            an evaluation report externally (PublishEvaluationReport) is
            approval-gated under §13 and not wired in v0.1 — the report below is
            the internal, measured record.
          </p>
        </Panel>
      </div>

      <Panel>
        <SectionTitle>Evaluation report</SectionTitle>
        {report.isPending ? (
          <Loading label="Loading report…" />
        ) : report.isError ? (
          <ApiErrorBox error={report.error} />
        ) : (
          <>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm sm:grid-cols-5">
              <Stat
                label="Mean reward"
                value={fmt(report.data.report_json.mean_reward)}
              />
              <Stat
                label="Median reward"
                value={fmt(report.data.report_json.median_reward)}
              />
              <Stat
                label="Mean length"
                value={fmt(report.data.report_json.mean_length)}
              />
              <Stat
                label="Success rate"
                value={fmt(report.data.report_json.success_rate)}
              />
              <Stat
                label="Episodes"
                value={String(report.data.report_json.episodes ?? '—')}
              />
            </dl>
            <pre className="mt-4 overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-relaxed text-platinum">
              {report.data.report_md}
            </pre>
          </>
        )}
      </Panel>

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

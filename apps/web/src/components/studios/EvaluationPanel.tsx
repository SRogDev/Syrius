import { useQuery } from '@tanstack/react-query';
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
  type EvaluationSuite,
  getEvaluation,
  listEvaluationSuites,
} from '#/lib/api';

/** Project Studio — Evaluation tab. Suites are listed for real; runs
 * are opened by id. A list-evaluations endpoint exists since Phase 7;
 * this tab is not wired to it yet.
 * The full Evaluation Studio lives at /evaluations/$id. */

export default function EvaluationPanel({ projectId }: { projectId: string }) {
  const suites = useQuery({
    queryKey: ['evaluation-suites'],
    queryFn: listEvaluationSuites,
  });
  const projectSuites = (suites.data ?? []).filter(
    (s: EvaluationSuite) => s.project_id === projectId,
  );
  const [evaluationId, setEvaluationId] = useState('');

  const evaluation = useQuery({
    queryKey: ['evaluation', evaluationId],
    queryFn: () => getEvaluation(evaluationId),
    enabled: evaluationId.length > 0,
  });

  return (
    <div className="space-y-4">
      <Panel>
        <SectionTitle>Evaluation suites</SectionTitle>
        {suites.isPending ? (
          <Loading label="Loading suites…" />
        ) : suites.isError ? (
          <ApiErrorBox error={suites.error} />
        ) : projectSuites.length === 0 ? (
          <p className="text-sm text-platinum">
            No evaluation suites for this project yet. Suites are created by the
            Evaluation Factory tools (CreateEvaluationSuite) — the web has no
            create-suite form in v0.1 because the backend exposes suite creation
            only as a tool run, not a REST route.
          </p>
        ) : (
          <ul className="space-y-2">
            {projectSuites.map((s) => (
              <li key={s.id} className="font-mono text-sm text-highlight">
                {s.name}{' '}
                <span className="text-muted">
                  — {JSON.stringify(s.criteria)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <Panel>
        <SectionTitle>Open evaluation run by id</SectionTitle>
        <label className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <span className="font-mono text-xs uppercase tracking-widest text-muted">
            Evaluation id
          </span>
          <input
            value={evaluationId}
            onChange={(e) => setEvaluationId(e.target.value.trim())}
            placeholder="evaluation run id"
            aria-label="Evaluation run id"
            className="h-10 flex-1 border border-line bg-bg px-3 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
          />
        </label>
        {evaluation.isPending && evaluationId ? (
          <Loading label="Loading evaluation…" />
        ) : null}
        {evaluation.isError ? <ApiErrorBox error={evaluation.error} /> : null}
        {evaluation.data ? (
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <span className="font-mono text-sm text-highlight">
              run {evaluation.data.id.slice(0, 8)}
            </span>
            <StatusBadge status={evaluation.data.status} />
            <Link
              to="/evaluations/$evaluationId"
              params={{ evaluationId: evaluation.data.id }}
              className="cursor-pointer font-mono text-xs uppercase tracking-widest text-highlight underline-offset-4 transition-colors duration-150 hover:underline"
            >
              Open Evaluation Studio →
            </Link>
          </div>
        ) : null}
        <p className="mt-3 text-sm text-muted">
          New runs are created from the Experiment Studio (Evaluate button) —
          evaluation is independent of training reward: success is a full
          500-step episode, not the training curve.
        </p>
      </Panel>
    </div>
  );
}

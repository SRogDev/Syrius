import { useMutation, useQuery } from '@tanstack/react-query';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
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
  createSpecification,
  type Environment,
  fetchAuditEvents,
  formalizeSpecification,
  getSpecification,
  listEnvironments,
  listEvaluationSuites,
  listTools,
  listWorkers,
  type Project,
} from '#/lib/api';
import { queryClient } from '#/lib/query-client';

/** Project Studio — Overview tab. Objective, formalized RL spec,
 * status, department progress (from the real tool registry — the
 * backend has no department model, so that gap is stated, not faked),
 * evaluation suites, workers, pending approvals, activity timeline. */

export default function ProjectOverview({ project }: { project: Project }) {
  const envs = useQuery({
    queryKey: ['environments'],
    queryFn: listEnvironments,
  });
  const tools = useQuery({ queryKey: ['tools'], queryFn: listTools });
  const suites = useQuery({
    queryKey: ['evaluation-suites'],
    queryFn: listEvaluationSuites,
  });
  const workers = useQuery({ queryKey: ['workers'], queryFn: listWorkers });
  const events = useQuery({
    queryKey: ['audit-events'],
    queryFn: fetchAuditEvents,
  });

  const projectEnvs = (envs.data ?? []).filter(
    (e: Environment) => e.project_id === project.id,
  );
  const projectSuites = (suites.data ?? []).filter(
    (s) => s.project_id === project.id,
  );
  const approvalGated = (tools.data ?? []).filter((t) => !t.implemented);
  const byDepartment = new Map<
    string,
    { total: number; implemented: number }
  >();
  for (const t of tools.data ?? []) {
    const entry = byDepartment.get(t.department) ?? {
      total: 0,
      implemented: 0,
    };
    entry.total += 1;
    if (t.implemented) entry.implemented += 1;
    byDepartment.set(t.department, entry);
  }

  return (
    <div className="space-y-4">
      <Panel>
        <SectionTitle>Objective + status</SectionTitle>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm sm:grid-cols-4">
          <Stat label="Project" value={project.name} />
          <Stat
            label="Status"
            value={<StatusBadge status={project.status} />}
          />
          <Stat label="Environments" value={projectEnvs.length} />
          <Stat label="Evaluation suites" value={projectSuites.length} />
        </dl>
        {project.description ? (
          <p className="mt-3 text-base text-platinum">{project.description}</p>
        ) : null}
      </Panel>

      <SpecSection projectId={project.id} />

      <Panel>
        <SectionTitle>Department progress</SectionTitle>
        {tools.isPending ? (
          <Loading label="Loading tool registry…" />
        ) : tools.isError ? (
          <ApiErrorBox error={tools.error} />
        ) : (
          <>
            <p className="mb-3 text-sm text-platinum">
              The backend has no department model in v0.1, so department
              progress is shown as the tool registry grouped by department — the
              real capability surface each department owns.
            </p>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm sm:grid-cols-4">
              {[...byDepartment.entries()].map(([dept, counts]) => (
                <Stat
                  key={dept}
                  label={dept}
                  value={`${counts.implemented} / ${counts.total} tools implemented`}
                />
              ))}
            </dl>
          </>
        )}
      </Panel>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel>
          <SectionTitle>Environments</SectionTitle>
          {envs.isPending ? (
            <Loading label="Loading environments…" />
          ) : envs.isError ? (
            <ApiErrorBox error={envs.error} />
          ) : projectEnvs.length === 0 ? (
            <p className="text-sm text-platinum">
              No environments for this project yet — create one from the
              Environment Studio tab.
            </p>
          ) : (
            <ul className="space-y-2">
              {projectEnvs.map((env) => (
                <li
                  key={env.id}
                  className="flex items-center justify-between gap-3 font-mono text-sm"
                >
                  <span className="text-highlight">
                    {env.name}{' '}
                    <span className="text-muted">({env.gym_id})</span>
                  </span>
                  <StatusBadge status={env.status} />
                </li>
              ))}
            </ul>
          )}
        </Panel>
        <Panel>
          <SectionTitle>Workers</SectionTitle>
          {workers.isPending ? (
            <Loading label="Loading workers…" />
          ) : workers.isError ? (
            <ApiErrorBox error={workers.error} />
          ) : workers.data.length === 0 ? (
            <p className="text-sm text-platinum">
              No workers registered. Start one with{' '}
              <code className="font-mono text-highlight">
                syrius-worker heartbeat
              </code>
              .
            </p>
          ) : (
            <ul className="space-y-2">
              {workers.data.map((w) => (
                <li
                  key={w.id}
                  className="flex items-center justify-between gap-3 font-mono text-sm"
                >
                  <span className="text-highlight">{w.name}</span>
                  <StatusBadge status={w.status} />
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <Panel>
        <SectionTitle>Pending approvals</SectionTitle>
        {tools.isPending ? (
          <Loading label="Loading approvals…" />
        ) : approvalGated.length === 0 ? (
          <p className="text-sm text-platinum">
            No approval-gated actions outstanding.
          </p>
        ) : (
          <ul className="space-y-2 text-sm">
            {approvalGated.map((t) => (
              <li key={t.name} className="font-mono text-sm text-platinum">
                <span className="text-highlight">{t.name}</span> —{' '}
                {t.not_implemented_reason}
              </li>
            ))}
          </ul>
        )}
        <p className="mt-3 text-sm text-muted">
          Human approval boundaries (§13) are recorded in the backend; no
          approval flow is exposed to the web yet — approval-gated tools return{' '}
          <code className="text-highlight">requires_human_approval</code> when
          run.
        </p>
      </Panel>

      <Panel>
        <SectionTitle>Activity timeline</SectionTitle>
        {events.isPending ? (
          <Loading label="Loading audit events…" />
        ) : events.isError ? (
          <ApiErrorBox error={events.error} />
        ) : events.data.length === 0 ? (
          <p className="text-sm text-platinum">No audit events recorded yet.</p>
        ) : (
          <ul className="space-y-2">
            {events.data.slice(0, 30).map((e) => (
              <li key={e.id} className="font-mono text-xs text-platinum">
                <span className="text-muted">{e.created_at ?? '—'}</span>{' '}
                <span className="text-highlight">{e.action}</span> ·{' '}
                {e.entity_type} {e.entity_id.slice(0, 8)}
              </li>
            ))}
          </ul>
        )}
        <p className="mt-3 text-sm text-muted">
          Engineering decisions are not a separate API resource in v0.1 —
          decisions live in the audit trail above and in the repo docs.
        </p>
      </Panel>

      <NotImplemented
        what="Active tasks, running workflows, experiments, evaluation results and artifacts on this tab"
        reason="The backend has no list endpoints for tasks, workflows or artifacts, and no department model, in v0.1. Experiments, evaluations and episodes now have list endpoints (Phase 7) — open them from the Environment, Experiments, Evaluation and Deliverables tabs, by id or from a create response."
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

function SpecSection({ projectId }: { projectId: string }) {
  const [title, setTitle] = useState('');
  const [problemText, setProblemText] = useState('');
  const [specId, setSpecId] = useState('');
  const [message, setMessage] = useState<string | null>(null);

  const specQuery = useQuery({
    queryKey: ['specification', specId],
    queryFn: () => getSpecification(specId),
    enabled: specId.length > 0,
  });

  const create = useMutation({
    mutationFn: () =>
      createSpecification({
        project_id: projectId,
        title: title.trim(),
        problem_text: problemText.trim(),
      }),
    onSuccess: (spec) => {
      setSpecId(spec.id);
      setTitle('');
      setProblemText('');
      setMessage(`Specification created: ${spec.id}`);
      void queryClient.invalidateQueries({
        queryKey: ['specification', spec.id],
      });
    },
    onError: (error: unknown) =>
      setMessage(
        error instanceof Error
          ? error.message
          : 'Could not create the specification.',
      ),
  });

  const formalize = useMutation({
    mutationFn: () => formalizeSpecification(specId),
    onSuccess: () => {
      setMessage(
        'Specification formalized — observation/action spaces, reward spec and approach filled from CartPole-v1.',
      );
      void queryClient.invalidateQueries({
        queryKey: ['specification', specId],
      });
    },
    onError: (error: unknown) =>
      setMessage(
        error instanceof Error
          ? error.message
          : 'Could not formalize the specification.',
      ),
  });

  const spec = specQuery.data;
  return (
    <Panel>
      <SectionTitle>RL problem specification</SectionTitle>
      {spec ? (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="font-display text-lg font-bold text-highlight">
              {spec.title}
            </h3>
            <StatusBadge status={spec.status} />
            <span className="font-mono text-xs text-muted">
              v{spec.version}
            </span>
          </div>
          {spec.problem_text ? (
            <p className="text-sm text-platinum">{spec.problem_text}</p>
          ) : null}
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm sm:grid-cols-3">
            <Stat
              label="Observation space"
              value={JSON.stringify(spec.observation_space)}
            />
            <Stat
              label="Action space"
              value={JSON.stringify(spec.action_space)}
            />
            <Stat label="Approach" value={JSON.stringify(spec.approach)} />
            <Stat
              label="Reward spec"
              value={JSON.stringify(spec.reward_spec)}
            />
            <Stat
              label="Gaps"
              value={spec.gaps.length === 0 ? 'none' : spec.gaps.join('; ')}
              tone={spec.gaps.length > 0 ? 'warn' : 'ok'}
            />
          </dl>
          <button
            type="button"
            onClick={() => formalize.mutate()}
            disabled={formalize.isPending}
            className="h-9 cursor-pointer border border-line px-4 font-mono text-xs uppercase tracking-widest text-highlight transition-colors duration-150 hover:border-platinum disabled:opacity-50"
          >
            {formalize.isPending ? 'Formalizing…' : 'Formalize (CartPole-v1)'}
          </button>
        </div>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (title.trim().length === 0) {
              setMessage('A specification needs a title.');
              return;
            }
            create.mutate();
          }}
          className="flex flex-col gap-3"
        >
          <p className="text-sm text-platinum">
            No specification loaded. Create one, or paste an existing
            specification id.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Balance CartPole for 500 steps"
              aria-label="Specification title"
              className="h-10 flex-1 border border-line bg-bg px-3 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
            />
            <input
              value={problemText}
              onChange={(e) => setProblemText(e.target.value)}
              placeholder="Problem statement (optional)"
              aria-label="Problem statement"
              className="h-10 flex-1 border border-line bg-bg px-3 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
            />
            <button
              type="submit"
              disabled={create.isPending}
              className="h-10 cursor-pointer border border-highlight bg-highlight px-4 font-mono text-xs uppercase tracking-widest text-bg transition-colors duration-150 hover:bg-platinum disabled:opacity-50"
            >
              {create.isPending ? 'Creating…' : 'Create spec'}
            </button>
          </div>
          <label className="flex items-center gap-2 font-mono text-xs text-platinum">
            Open existing spec id
            <input
              value={specId}
              onChange={(e) => setSpecId(e.target.value.trim())}
              placeholder="specification id"
              aria-label="Existing specification id"
              className="h-9 flex-1 border border-line bg-bg px-3 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
            />
          </label>
          {specQuery.isError ? (
            <p role="alert" className="font-mono text-sm text-amber-300">
              {specQuery.error instanceof Error
                ? specQuery.error.message
                : 'Specification not found.'}
            </p>
          ) : null}
        </form>
      )}
      {message ? (
        <p className="mt-3 font-mono text-sm text-platinum">{message}</p>
      ) : null}
    </Panel>
  );
}

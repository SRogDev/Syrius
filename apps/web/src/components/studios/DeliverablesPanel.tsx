import { useMutation, useQuery } from '@tanstack/react-query';
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
  createPolicy,
  exportPolicy,
  getJob,
  getPolicy,
  listCheckpoints,
} from '#/lib/api';

/** Project Studio — Deliverables / Deployment Factory tab.
 * Policy lookup, reproducibility manifest display, export wired to
 * POST /api/v1/policies/{id}/export with job polling. The delivery
 * package download is honestly unavailable: the API serves artifact
 * metadata only, not artifact bytes. */

export default function DeliverablesPanel({
  projectId,
}: {
  projectId: string;
}) {
  void projectId;
  const [policyId, setPolicyId] = useState('');
  const [experimentId, setExperimentId] = useState('');
  const [jobId, setJobId] = useState('');

  const policy = useQuery({
    queryKey: ['policy', policyId],
    queryFn: () => getPolicy(policyId),
    enabled: policyId.length > 0,
  });
  const checkpoints = useQuery({
    queryKey: ['checkpoints', experimentId],
    queryFn: () => listCheckpoints(experimentId),
    enabled: experimentId.length > 0,
  });
  const job = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJob(jobId),
    enabled: jobId.length > 0,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'queued' || status === 'running' ? 2000 : false;
    },
  });

  const [message, setMessage] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () => createPolicy({ experiment_id: experimentId.trim() }),
    onSuccess: (p) => {
      setPolicyId(p.id);
      setMessage(
        `Policy created: ${p.id} (latest checkpoint of the experiment).`,
      );
    },
    onError: (error: unknown) =>
      setMessage(
        error instanceof Error ? error.message : 'Could not create the policy.',
      ),
  });

  const exportMut = useMutation({
    mutationFn: () => exportPolicy(policyId),
    onSuccess: (result) => {
      setJobId(result.job_id);
      setMessage(
        `Export enqueued: job ${result.job_id} (status ${result.status}).`,
      );
    },
    onError: (error: unknown) =>
      setMessage(
        error instanceof Error ? error.message : 'Could not start the export.',
      ),
  });

  const manifest = policy.data?.manifest ?? {};

  return (
    <div className="space-y-4">
      <Panel>
        <SectionTitle>
          Policy — lookup or create from an experiment
        </SectionTitle>
        <div className="flex flex-col gap-3">
          <label className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <span className="font-mono text-xs uppercase tracking-widest text-muted">
              Policy id
            </span>
            <input
              value={policyId}
              onChange={(e) => setPolicyId(e.target.value.trim())}
              placeholder="policy id"
              aria-label="Policy id"
              className="h-10 flex-1 border border-line bg-bg px-3 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
            />
          </label>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <label className="flex-1">
              <span className="mb-1 block font-mono text-[11px] uppercase tracking-widest text-muted">
                Or create a policy from experiment id (uses its latest
                checkpoint)
              </span>
              <input
                value={experimentId}
                onChange={(e) => setExperimentId(e.target.value.trim())}
                placeholder="experiment id"
                aria-label="Experiment id for policy creation"
                className="h-10 w-full border border-line bg-bg px-3 font-mono text-sm text-highlight placeholder:text-muted focus:outline-2 focus:outline-highlight"
              />
            </label>
            <button
              type="button"
              onClick={() => create.mutate()}
              disabled={create.isPending || experimentId.trim().length === 0}
              className="h-10 cursor-pointer border border-line px-4 font-mono text-xs uppercase tracking-widest text-highlight transition-colors duration-150 hover:border-platinum disabled:opacity-50"
            >
              {create.isPending ? 'Creating…' : 'Create policy'}
            </button>
          </div>
        </div>
        {policy.isError ? <ApiErrorBox error={policy.error} /> : null}
        {policy.isPending && policyId ? (
          <Loading label="Loading policy…" />
        ) : null}
        {policy.data ? (
          <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm sm:grid-cols-4">
            <Stat label="Name" value={policy.data.name} />
            <Stat label="Algorithm" value={policy.data.algorithm} />
            <Stat
              label="Status"
              value={<StatusBadge status={policy.data.status} />}
            />
            <Stat label="Artifact" value={policy.data.artifact_id ?? '—'} />
          </dl>
        ) : null}
        {message ? (
          <p className="mt-3 font-mono text-sm text-platinum">{message}</p>
        ) : null}
        {checkpoints.data && checkpoints.data.length > 0 ? (
          <p className="mt-3 font-mono text-xs text-muted">
            Checkpoints for this experiment:{' '}
            {checkpoints.data.map((c) => `step ${c.step}`).join(', ')}
          </p>
        ) : null}
      </Panel>

      {policy.data ? (
        <Panel>
          <SectionTitle>Reproducibility manifest</SectionTitle>
          {Object.keys(manifest).length === 0 ? (
            <p className="text-sm text-platinum">
              This policy has no manifest yet — the manifest is written by the
              Deployment Factory at export time.
            </p>
          ) : (
            <pre className="overflow-x-auto whitespace-pre-wrap break-words font-mono text-xs leading-relaxed text-platinum">
              {JSON.stringify(manifest, null, 2)}
            </pre>
          )}
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => exportMut.mutate()}
              disabled={exportMut.isPending}
              className="h-10 cursor-pointer border border-highlight bg-highlight px-4 font-mono text-xs uppercase tracking-widest text-bg transition-colors duration-150 hover:bg-platinum disabled:opacity-50"
            >
              {exportMut.isPending ? 'Exporting…' : 'Export delivery package'}
            </button>
            {job.data ? (
              <span className="font-mono text-sm text-highlight">
                Export job <StatusBadge status={job.data.status} />
                {job.data.error ? (
                  <span className="ml-2 text-amber-300">{job.data.error}</span>
                ) : null}
              </span>
            ) : null}
          </div>
          <p className="mt-3 text-sm text-muted">
            Export enqueues a job (the browser never packages a model). When the
            job completes, the package (final_model.zip + manifest.json +
            README.md) exists in artifact storage.
          </p>
          <NotImplemented
            what="Delivery package download"
            reason="The API serves artifact metadata (GET /artifacts/{id}) but no artifact bytes endpoint exists in v0.1, so the browser cannot download the zip yet. The manifest above and the export job status are the real, verifiable surface."
          />
        </Panel>
      ) : null}
    </div>
  );
}

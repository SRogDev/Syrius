/** Typed API client over the real /api/v1/ routes (see routers.py).
 * Contracts mirror packages/api-client/src/types.ts (OpenAPI-generated);
 * routes missing from that file are typed from routers.py and noted.
 * No mock data: every function hits the live API and throws ApiError
 * (server detail) or a plain Error (unreachable) on failure. */

import type {
  MetricsOut,
  TrainingConfig,
} from '../../../../packages/api-client/src/types';

export type { MetricsOut, TrainingConfig };

export interface HealthResponse {
  service: string;
  version: string;
  environment: string;
  status: 'ok' | 'degraded';
  db: 'ok' | 'unavailable';
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  status: string;
  workspace_id: string | null;
}

export interface Specification {
  id: string;
  project_id: string;
  title: string;
  problem_text: string | null;
  observation_space: Record<string, unknown>;
  action_space: Record<string, unknown>;
  episode_structure: Record<string, unknown>;
  constraints: Record<string, unknown>;
  reward_spec: Record<string, unknown>;
  approach: Record<string, unknown>;
  status: string;
  gaps: string[];
  version: number;
}

export interface Environment {
  id: string;
  project_id: string;
  name: string;
  gym_id: string;
  version: number;
  config: Record<string, unknown>;
  status: string;
}

export interface Experiment {
  id: string;
  project_id: string;
  environment_id: string;
  name: string;
  algorithm: string;
  config: Record<string, unknown>;
  status: string;
}

export interface Episode {
  id: string;
  environment_id: string;
  length: number;
  total_reward: number;
  success: boolean | null;
  seed: number;
  trace_artifact_id: string | null;
}

export interface TraceStep {
  step: number;
  observation: number[];
  action: number;
  reward: number;
  terminated: boolean;
  truncated: boolean;
  info: Record<string, string>;
}

export interface EpisodeTrace {
  episode_id: string;
  gym_id: string;
  seed: number;
  steps: TraceStep[];
}

export interface EvaluationRun {
  id: string;
  experiment_id: string;
  policy_id: string | null;
  status: string;
  metrics: Record<string, unknown>;
}

export interface EvaluationReport {
  report_json: {
    evaluation_run_id: string;
    experiment_id: string;
    status: string;
    mean_reward: number | null;
    median_reward: number | null;
    mean_length: number | null;
    success_rate: number | null;
    episodes: number | null;
  };
  report_md: string;
}

export interface Checkpoint {
  id: string;
  step: number;
  artifact_id: string;
  created_at: string | null;
}

export interface Policy {
  id: string;
  experiment_id: string;
  checkpoint_id: string | null;
  name: string;
  algorithm: string;
  artifact_id: string | null;
  status: string;
  manifest: Record<string, unknown>;
}

export interface Job {
  id: string;
  kind: string;
  status: string;
  retry_count: number;
  result: Record<string, unknown>;
  error: string | null;
}

export interface ToolDefinition {
  name: string;
  department: string;
  description: string;
  implemented: boolean;
  not_implemented_reason: string;
}

export interface WorkerRow {
  id: string;
  name: string;
  status: string;
  last_heartbeat_at: string | null;
}

export interface EvaluationSuite {
  id: string;
  project_id: string;
  name: string;
  criteria: Record<string, unknown>;
}

export interface AuditEvent {
  id: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: Record<string, unknown>;
  created_at: string | null;
}

export interface TrainResponse {
  experiment_id: string;
  training_run_id: string;
  job_id: string;
  status: string;
}

export class ApiError extends Error {
  readonly status: number;
  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
  }
}

function apiBase(): string {
  // In dev, Vite proxies /api to the FastAPI server on :8000. In a built
  // deployment, point VITE_API_URL at the API origin.
  return import.meta.env.VITE_API_URL ?? '';
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBase()}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
      ...init,
    });
  } catch {
    throw new Error(`API unreachable — is the API running on :8000? (${path})`);
  }
  if (!response.ok) {
    let detail = `API request failed: ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === 'string') detail = body.detail;
      else if (Array.isArray(body.detail)) detail = JSON.stringify(body.detail);
    } catch {
      // Keep the status-based message.
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

const post = <T>(path: string, body: unknown): Promise<T> =>
  apiFetch<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}) });

// --- Health (Phase 0) -------------------------------------------------------

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/api/v1/health');
}

// --- Projects ---------------------------------------------------------------

export async function listProjects(): Promise<Project[]> {
  return apiFetch<Project[]>('/api/v1/projects');
}

export async function createProject(input: {
  name: string;
  description?: string;
}): Promise<Project> {
  return post<Project>('/api/v1/projects', {
    name: input.name,
    description: input.description ?? '',
  });
}

export async function getProject(projectId: string): Promise<Project> {
  return apiFetch<Project>(`/api/v1/projects/${projectId}`);
}

// --- Specifications (RL Architect) ------------------------------------------

export async function createSpecification(input: {
  project_id: string;
  title: string;
  problem_text?: string;
}): Promise<Specification> {
  return post<Specification>('/api/v1/specifications', {
    project_id: input.project_id,
    title: input.title,
    problem_text: input.problem_text ?? '',
  });
}

export async function getSpecification(specId: string): Promise<Specification> {
  return apiFetch<Specification>(`/api/v1/specifications/${specId}`);
}

export async function formalizeSpecification(
  specId: string,
  gymId = 'CartPole-v1',
): Promise<Specification> {
  return post<Specification>(`/api/v1/specifications/${specId}/formalize`, {
    gym_id: gymId,
  });
}

// --- Environments (Environment Factory) -------------------------------------

/** NOTE: the backend has no list-by-project endpoint; callers filter
 * the full list client-side by project_id. */
export async function listEnvironments(): Promise<Environment[]> {
  return apiFetch<Environment[]>('/api/v1/environments');
}

export async function createEnvironment(input: {
  project_id: string;
  name: string;
  gym_id?: string;
  specification_id?: string | null;
  config?: Record<string, unknown>;
}): Promise<Environment> {
  return post<Environment>('/api/v1/environments', {
    project_id: input.project_id,
    name: input.name,
    gym_id: input.gym_id ?? 'CartPole-v1',
    specification_id: input.specification_id ?? null,
    config: input.config ?? {},
  });
}

export async function getEnvironment(envId: string): Promise<Environment> {
  return apiFetch<Environment>(`/api/v1/environments/${envId}`);
}

export async function validateEnvironment(
  gymId: string,
  seed = 0,
): Promise<Record<string, unknown>> {
  return post<Record<string, unknown>>('/api/v1/environments/validate', {
    gym_id: gymId,
    seed,
  });
}

// --- Experiments / training (Experiment Factory) -----------------------------

/** NOTE: the backend has no list-experiments endpoint; experiments are
 * opened by id (from a training workflow, a create response, or a
 * pasted id). */
export async function createExperiment(input: {
  project_id: string;
  environment_id: string;
  name: string;
  specification_id?: string | null;
  algorithm?: string;
  config?: TrainingConfig;
}): Promise<Experiment> {
  return post<Experiment>('/api/v1/experiments', {
    project_id: input.project_id,
    environment_id: input.environment_id,
    name: input.name,
    specification_id: input.specification_id ?? null,
    algorithm: input.algorithm ?? 'PPO',
    config: input.config ?? {},
  });
}

export async function getExperiment(experimentId: string): Promise<Experiment> {
  return apiFetch<Experiment>(`/api/v1/experiments/${experimentId}`);
}

export async function trainExperiment(
  experimentId: string,
  config?: TrainingConfig | null,
): Promise<TrainResponse> {
  return post<TrainResponse>(`/api/v1/experiments/${experimentId}/train`, {
    config: config ?? null,
  });
}

/** Baseline run (random policy). Returns the enqueued job. */
export async function baselineExperiment(
  experimentId: string,
  episodes = 20,
  seed = 0,
): Promise<{ experiment_id: string; job_id: string; status: string }> {
  return post(`/api/v1/experiments/${experimentId}/baseline`, {
    episodes,
    seed,
  });
}

export async function getExperimentMetrics(
  experimentId: string,
): Promise<MetricsOut> {
  return apiFetch<MetricsOut>(`/api/v1/experiments/${experimentId}/metrics`);
}

export async function evaluateExperiment(
  experimentId: string,
  input: {
    policy_id?: string | null;
    episodes?: number;
    seed?: number;
    deterministic?: boolean;
  },
): Promise<{ evaluation_run_id: string; job_id: string; status: string }> {
  return post(`/api/v1/experiments/${experimentId}/evaluate`, {
    policy_id: input.policy_id ?? null,
    episodes: input.episodes ?? 20,
    seed: input.seed ?? 100,
    deterministic: input.deterministic ?? true,
  });
}

export async function listCheckpoints(
  experimentId: string,
): Promise<Checkpoint[]> {
  return apiFetch<Checkpoint[]>(
    `/api/v1/experiments/${experimentId}/checkpoints`,
  );
}

// --- Evaluations ------------------------------------------------------------

/** NOTE: the backend has no list-evaluations endpoint; evaluation runs
 * are opened by id (from an evaluate response or a pasted id). */
export async function getEvaluation(
  evaluationId: string,
): Promise<EvaluationRun> {
  return apiFetch<EvaluationRun>(`/api/v1/evaluations/${evaluationId}`);
}

export async function getEvaluationReport(
  evaluationId: string,
): Promise<EvaluationReport> {
  return apiFetch<EvaluationReport>(
    `/api/v1/evaluations/${evaluationId}/report`,
  );
}

export async function listEvaluationSuites(): Promise<EvaluationSuite[]> {
  return apiFetch<EvaluationSuite[]>('/api/v1/evaluation-suites');
}

// --- Episodes ---------------------------------------------------------------

/** NOTE: the backend has no list-episodes endpoint; episodes are opened
 * by id (from a RecordEpisode tool result or a pasted id). */
export async function getEpisode(episodeId: string): Promise<Episode> {
  return apiFetch<Episode>(`/api/v1/episodes/${episodeId}`);
}

export async function getEpisodeTrace(
  episodeId: string,
): Promise<EpisodeTrace> {
  return apiFetch<EpisodeTrace>(`/api/v1/episodes/${episodeId}/trace`);
}

/** Record one fresh episode (random policy) via the RecordEpisode tool.
 * Returns the new episode id so the Studio can open its trace. */
export async function recordEpisode(
  environmentId: string,
  seed = 0,
): Promise<{
  episode_id: string;
  length: number;
  reward: number;
  trace_artifact_id: string;
}> {
  return runTool('RecordEpisode', { environment_id: environmentId, seed });
}

// --- Policies / export (Deployment Factory) ---------------------------------

export async function createPolicy(input: {
  experiment_id: string;
  checkpoint_id?: string | null;
  name?: string;
}): Promise<Policy> {
  return post<Policy>('/api/v1/policies', {
    experiment_id: input.experiment_id,
    checkpoint_id: input.checkpoint_id ?? null,
    name: input.name,
  });
}

export async function getPolicy(policyId: string): Promise<Policy> {
  return apiFetch<Policy>(`/api/v1/policies/${policyId}`);
}

export async function exportPolicy(
  policyId: string,
): Promise<{ policy_id: string; job_id: string; status: string }> {
  return post(`/api/v1/policies/${policyId}/export`, {});
}

export async function getArtifact(
  artifactId: string,
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/api/v1/artifacts/${artifactId}`);
}

// --- Jobs -------------------------------------------------------------------

export async function getJob(jobId: string): Promise<Job> {
  return apiFetch<Job>(`/api/v1/jobs/${jobId}`);
}

export async function cancelJob(jobId: string): Promise<Job> {
  return post<Job>(`/api/v1/jobs/${jobId}/cancel`, {});
}

// --- Capabilities / tools ---------------------------------------------------

export async function listTools(): Promise<ToolDefinition[]> {
  return apiFetch<ToolDefinition[]>('/api/v1/capabilities/tools');
}

export async function runTool<T = Record<string, unknown>>(
  name: string,
  payload: Record<string, unknown>,
): Promise<T> {
  return post<T>(
    `/api/v1/capabilities/tools/${encodeURIComponent(name)}/run`,
    payload,
  );
}

// --- Workers / events -------------------------------------------------------

export async function listWorkers(): Promise<WorkerRow[]> {
  return apiFetch<WorkerRow[]>('/api/v1/workers');
}

/** Fetch the recent audit/provenance events. The backend serves them as
 * one SSE burst (GET /api/v1/events); this reads the whole stream body
 * and parses the `data:` lines. */
export async function fetchAuditEvents(): Promise<AuditEvent[]> {
  let text: string;
  try {
    const response = await fetch(`${apiBase()}/api/v1/events`);
    text = await response.text();
  } catch {
    throw new Error(
      'API unreachable — is the API running on :8000? (/api/v1/events)',
    );
  }
  const events: AuditEvent[] = [];
  for (const line of text.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed.startsWith('data:')) continue;
    try {
      events.push(JSON.parse(trimmed.slice(5).trim()) as AuditEvent);
    } catch {
      // Ignore malformed SSE lines; the stream is best-effort history.
    }
  }
  return events;
}

// --- Workflows --------------------------------------------------------------

export async function createWorkflow(input: {
  project_id: string;
  name?: string;
  kind?: string;
  definition?: Record<string, unknown>;
}): Promise<{
  id: string;
  project_id: string;
  name: string;
  kind: string;
  status: string;
}> {
  return post('/api/v1/workflows', {
    project_id: input.project_id,
    name: input.name ?? 'training-workflow',
    kind: input.kind ?? 'training',
    definition: input.definition ?? {},
  });
}

export async function getWorkflow(
  workflowId: string,
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/api/v1/workflows/${workflowId}`);
}

export async function runWorkflow(
  workflowId: string,
  payload: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return post(`/api/v1/workflows/${workflowId}/run`, payload);
}

// GENERATED — do not edit by hand.
// Source: the Syrius API OpenAPI schema (scripts/gen_api_client.py).
// Regenerate with: uv run --project apps/api python scripts/gen_api_client.py

export interface EnvironmentCreate {
  project_id: string;
  name: string;
  gym_id?: string;
  specification_id?: string | null;
  config?: Record<string, unknown>;
}

export interface EnvironmentValidationOut {
  gym_id: string;
  valid: boolean;
  observation_space: Record<string, unknown>;
  action_space: Record<string, unknown>;
  smoke_episode_length: number;
  smoke_episode_reward: number;
  warnings?: string[];
  checked_with?: string;
}

export interface EvaluateRequest {
  policy_id?: string | null;
  episodes?: number;
  seed?: number;
  deterministic?: boolean;
}

export interface ExperimentCreate {
  project_id: string;
  environment_id: string;
  name: string;
  specification_id?: string | null;
  algorithm?: string;
  config?: TrainingConfig;
}

export interface HTTPValidationError {
  detail?: ValidationError[];
}

export interface MetricsOut {
  experiment_id: string;
  training_run_id?: string | null;
  status: string;
  current_step?: number;
  total_timesteps?: number;
  metrics?: Record<string, unknown>;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  workspace_id?: string | null;
}

export interface SpecificationCreate {
  project_id: string;
  title: string;
  problem_text?: string;
}

export interface TrainRequest {
  config?: TrainingConfig | null;
}

export interface TrainingConfig {
  env_id?: string;
  algorithm?: string;
  seed?: number;
  total_timesteps?: number;
  learning_rate?: number;
  n_steps?: number;
  batch_size?: number;
  n_epochs?: number;
  gamma?: number;
  gae_lambda?: number;
  clip_range?: number;
  eval_episodes?: number;
  eval_deterministic?: boolean;
  eval_seed?: number;
  version?: number;
}

export interface ValidationError {
  loc: string | number[];
  msg: string;
  type: string;
  input?: unknown;
  ctx?: Record<string, unknown>;
}

// Operation map (method + path -> response type).
export interface ApiOperations {
  get_artifact_api_v1_artifacts__artifact_id__get: {
    method: 'get';
    path: '/api/v1/artifacts/{artifact_id}';
    response: Record<string, unknown>;
  };
  download_artifact_api_v1_artifacts__artifact_id__download_get: {
    method: 'get';
    path: '/api/v1/artifacts/{artifact_id}/download';
    response: unknown;
  };
  seed_tools_api_v1_capabilities_seed_tools_post: {
    method: 'post';
    path: '/api/v1/capabilities/seed-tools';
    response: Record<string, unknown>;
  };
  list_tools_api_v1_capabilities_tools_get: {
    method: 'get';
    path: '/api/v1/capabilities/tools';
    response: Record<string, unknown>[];
  };
  run_tool_endpoint_api_v1_capabilities_tools__name__run_post: {
    method: 'post';
    path: '/api/v1/capabilities/tools/{name}/run';
    response: Record<string, unknown>;
  };
  list_environments_api_v1_environments_get: {
    method: 'get';
    path: '/api/v1/environments';
    response: Record<string, unknown>[];
  };
  create_environment_api_v1_environments_post: {
    method: 'post';
    path: '/api/v1/environments';
    response: Record<string, unknown>;
  };
  validate_environment_api_v1_environments_validate_post: {
    method: 'post';
    path: '/api/v1/environments/validate';
    response: EnvironmentValidationOut;
  };
  get_environment_api_v1_environments__env_id__get: {
    method: 'get';
    path: '/api/v1/environments/{env_id}';
    response: Record<string, unknown>;
  };
  list_episodes_api_v1_episodes_get: {
    method: 'get';
    path: '/api/v1/episodes';
    response: Record<string, unknown>[];
  };
  get_episode_api_v1_episodes__episode_id__get: {
    method: 'get';
    path: '/api/v1/episodes/{episode_id}';
    response: Record<string, unknown>;
  };
  get_episode_trace_api_v1_episodes__episode_id__trace_get: {
    method: 'get';
    path: '/api/v1/episodes/{episode_id}/trace';
    response: Record<string, unknown>;
  };
  list_evaluation_suites_api_v1_evaluation_suites_get: {
    method: 'get';
    path: '/api/v1/evaluation-suites';
    response: Record<string, unknown>[];
  };
  list_evaluations_api_v1_evaluations_get: {
    method: 'get';
    path: '/api/v1/evaluations';
    response: Record<string, unknown>[];
  };
  get_evaluation_api_v1_evaluations__evaluation_id__get: {
    method: 'get';
    path: '/api/v1/evaluations/{evaluation_id}';
    response: Record<string, unknown>;
  };
  get_evaluation_report_api_v1_evaluations__evaluation_id__report_get: {
    method: 'get';
    path: '/api/v1/evaluations/{evaluation_id}/report';
    response: Record<string, unknown>;
  };
  stream_events_api_v1_events_get: {
    method: 'get';
    path: '/api/v1/events';
    response: unknown;
  };
  list_experiments_api_v1_experiments_get: {
    method: 'get';
    path: '/api/v1/experiments';
    response: Record<string, unknown>[];
  };
  create_experiment_api_v1_experiments_post: {
    method: 'post';
    path: '/api/v1/experiments';
    response: Record<string, unknown>;
  };
  get_experiment_api_v1_experiments__experiment_id__get: {
    method: 'get';
    path: '/api/v1/experiments/{experiment_id}';
    response: Record<string, unknown>;
  };
  baseline_experiment_api_v1_experiments__experiment_id__baseline_post: {
    method: 'post';
    path: '/api/v1/experiments/{experiment_id}/baseline';
    response: Record<string, unknown>;
  };
  list_checkpoints_api_v1_experiments__experiment_id__checkpoints_get: {
    method: 'get';
    path: '/api/v1/experiments/{experiment_id}/checkpoints';
    response: Record<string, unknown>[];
  };
  evaluate_experiment_api_v1_experiments__experiment_id__evaluate_post: {
    method: 'post';
    path: '/api/v1/experiments/{experiment_id}/evaluate';
    response: Record<string, unknown>;
  };
  experiment_events_api_v1_experiments__experiment_id__events_get: {
    method: 'get';
    path: '/api/v1/experiments/{experiment_id}/events';
    response: unknown;
  };
  experiment_history_api_v1_experiments__experiment_id__history_get: {
    method: 'get';
    path: '/api/v1/experiments/{experiment_id}/history';
    response: Record<string, unknown>;
  };
  experiment_metrics_api_v1_experiments__experiment_id__metrics_get: {
    method: 'get';
    path: '/api/v1/experiments/{experiment_id}/metrics';
    response: MetricsOut;
  };
  train_experiment_api_v1_experiments__experiment_id__train_post: {
    method: 'post';
    path: '/api/v1/experiments/{experiment_id}/train';
    response: Record<string, unknown>;
  };
  health_v1_api_v1_health_get: {
    method: 'get';
    path: '/api/v1/health';
    response: Record<string, string>;
  };
  get_job_api_v1_jobs__job_id__get: {
    method: 'get';
    path: '/api/v1/jobs/{job_id}';
    response: Record<string, unknown>;
  };
  cancel_job_endpoint_api_v1_jobs__job_id__cancel_post: {
    method: 'post';
    path: '/api/v1/jobs/{job_id}/cancel';
    response: Record<string, unknown>;
  };
  create_policy_api_v1_policies_post: {
    method: 'post';
    path: '/api/v1/policies';
    response: Record<string, unknown>;
  };
  get_policy_api_v1_policies__policy_id__get: {
    method: 'get';
    path: '/api/v1/policies/{policy_id}';
    response: Record<string, unknown>;
  };
  export_policy_api_v1_policies__policy_id__export_post: {
    method: 'post';
    path: '/api/v1/policies/{policy_id}/export';
    response: Record<string, unknown>;
  };
  list_projects_api_v1_projects_get: {
    method: 'get';
    path: '/api/v1/projects';
    response: Record<string, unknown>[];
  };
  create_project_api_v1_projects_post: {
    method: 'post';
    path: '/api/v1/projects';
    response: Record<string, unknown>;
  };
  get_project_api_v1_projects__project_id__get: {
    method: 'get';
    path: '/api/v1/projects/{project_id}';
    response: Record<string, unknown>;
  };
  create_specification_api_v1_specifications_post: {
    method: 'post';
    path: '/api/v1/specifications';
    response: Record<string, unknown>;
  };
  get_specification_api_v1_specifications__spec_id__get: {
    method: 'get';
    path: '/api/v1/specifications/{spec_id}';
    response: Record<string, unknown>;
  };
  formalize_specification_api_v1_specifications__spec_id__formalize_post: {
    method: 'post';
    path: '/api/v1/specifications/{spec_id}/formalize';
    response: Record<string, unknown>;
  };
  list_workers_api_v1_workers_get: {
    method: 'get';
    path: '/api/v1/workers';
    response: Record<string, unknown>[];
  };
  create_workflow_api_v1_workflows_post: {
    method: 'post';
    path: '/api/v1/workflows';
    response: Record<string, unknown>;
  };
  get_workflow_api_v1_workflows__workflow_id__get: {
    method: 'get';
    path: '/api/v1/workflows/{workflow_id}';
    response: Record<string, unknown>;
  };
  cancel_workflow_api_v1_workflows__workflow_id__cancel_post: {
    method: 'post';
    path: '/api/v1/workflows/{workflow_id}/cancel';
    response: Record<string, unknown>;
  };
  run_workflow_api_v1_workflows__workflow_id__run_post: {
    method: 'post';
    path: '/api/v1/workflows/{workflow_id}/run';
    response: Record<string, unknown>;
  };
  health_health_get: {
    method: 'get';
    path: '/health';
    response: Record<string, string>;
  };
}

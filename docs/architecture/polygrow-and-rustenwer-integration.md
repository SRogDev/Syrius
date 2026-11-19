# Syrius — Integration with Polygrow and Rustenwer

- **Date:** 2026-11-19
- **Directive:** Roger, "Rustenwer & Syrius — Architectural Evolution Toward Polygrow's Intelligence Infrastructure"
- **Companion documents:** `cross-system-report.md` (same directory — the §13 audit this doc builds on); Rustenwer `docs/architecture/polygrow-and-syrius-integration.md` (the mirror doc); Polygrow Spec B "Intelligence Compute Platform" (`docs/plans/phase 2/`, plan-only).

## What Polygrow is

Polygrow is the central intelligence-production platform. It owns the shared
infrastructure every specialized system runs on: central intelligence
orchestration, general compute job lifecycle, Modal integration and
credentials, remote CPU/GPU execution, tenant identity and authorization,
shared budgets/credits/usage, general artifact infrastructure, the shared
model/intelligence resource lifecycle, the general Developer API, the
user-facing intelligence-production experience, and Mind integration.

What Polygrow can actually do at the model level today is almost nothing:
it selects and calls third-party models through OpenRouter (LLM router +
Jev), learns prompt-level Skills, and evaluates agents. It has no model
registry, no training/fine-tuning code, no Developer API, and no Modal
code — the entire Intelligence Compute Platform (Spec B) is plan-only.
That is why Syrius exists in this ecosystem: Polygrow orchestrates,
Syrius engineers learning through interaction.

## What the Polygrow intelligence / compute platform owns

- The `intelligence/` domain (Spec B, plan-only): `Intelligence` (9 states),
  immutable `IntelligenceVersion`, `ComputeJob` (10 states), `ModelEndpoint`,
  `Dataset`, `Experiment`, `IntelligenceUsage`.
- The `ComputeProvider` adapter behind which Modal hides; one
  Polygrow-managed Modal Workspace for all tenants, never one per user.
- Workload profiles (`cpu_task`, `memory_task`, `gpu_inference`,
  `gpu_training`, `sandbox_execution`, `batch_processing`,
  `persistent_server`) with hard resource/budget limits.
- Credit reserve → execute → reconcile; sandboxes with explicit
  lifetime/isolation/cleanup; inference only via the Polygrow Developer API.
- Supabase/Postgres stays the canonical source of truth for product and
  lifecycle state.

Spec B must work independently of Rustenwer and Syrius (§2.3). Integration
is optional and additive — Polygrow never _requires_ this repo.

## Why Modal was selected

Polygrow chose Modal as its initial and currently exclusive remote compute
provider for intelligence fabrication workloads: CPU/GPU jobs, inference,
training and fine-tuning, batch processing, evaluation, RL experiments,
controlled remote execution, model serving where appropriate. Polygrow
manages the control plane; Modal executes the workloads.

Consequences for Syrius:

- **Modal is the only initial remote compute provider.** Do not introduce
  RunPod, AWS, Kubernetes, or any other remote provider. There is no
  remote-provider code in this repo at all today — the only trace is the
  string `"provision_gpu_instance"` inside the `PAID_COMPUTE_ACTIONS`
  boundary (`apps/api/src/syrius_api/capabilities.py:141`), explicitly
  "not implemented in v0.1".
- No Modal credentials in this repo, ever. Credentials live server-side
  in Polygrow; a transitional adapter reads them from the environment
  only, never in code, prompts, logs, or artifacts.
- Local execution stays: local dev, lightweight processing, and tests
  never need Modal. The CartPole slice runs on CPU by design.

## What Syrius does

Syrius is the specialized reinforcement-learning system: environments,
simulations, rollouts, policies, RL algorithms, training, and evaluation.
Concretely, at `main` @ `0745711` (v0.1, Phases 0–7):

- **Environments** — Gymnasium adapter (`gym.make(gym_id)`,
  `check_env` validation); built-in registry of 6 ids, only CartPole-v1
  validated end-to-end. No custom-env registration yet.
- **Simulation / rollouts** — `run_episode` with per-step traces,
  random baselines, 10,000-step safety cap.
- **Training (PPO only)** — SB3 `PPO("MlpPolicy", …)`, CPU only,
  20,000-step default; SAC exists as a label only.
- **Checkpoints** — exactly one per run (`final_model.zip`); selection =
  latest by step. No promotion, staging, or rollback yet.
- **Independent evaluation** — fresh `PPO.load()`, fresh rollouts,
  success = full 500-step episode, decoupled from training reward;
  random-baseline comparison; `report.json`/`report.md`.
- **Policy packaging** — `manifest.json` + zip + README, independently
  validated by fresh load + rollouts in a tempdir.
- **71-tool department registry** — 65 implemented handlers spanning
  spec → env → experiment → evaluation → deployment, with honest
  `not_implemented` + human-approval gating for the rest.
- **Jobs** — Postgres-backed queue (lease/heartbeat/retry/cancel) +
  worker CLI; the API never trains inside a request handler; SSE progress.

Measured (Phase 7 E2E, 2026-11-14): baseline mean 21.90; PPO 20k steps
in 54.3 s; eval mean 498.70/500, success 0.95 (19/20); export
independently validated mean 492.80, success 0.80.

## What Rustenwer does (and how it complements Syrius)

Rustenwer is the specialized model-engineering system: model creation,
adaptation, training, fine-tuning, optimization, evaluation, and packaging.
Its asset is the framework-free domain core in `shared/`: a diagnosis
pipeline that decides DO NOT TRAIN before spending compute, a method
recommendation engine with vetoes as negative-search data, hypothesis-driven
experiments with budgets and Pareto stopping policies, experiment memory
that never re-proposes a ruled-out method@version, and an immutable
`IntelligenceVersion` registry with a deterministic promotion gate and
OpenAI-compat serving.

Rustenwer complements Syrius; it does not compete with it:

- Rustenwer engineers intelligence through **model construction and
  adaptation**. Syrius engineers intelligence through **interaction,
  reinforcement, and policy learning**.
- A possible composition (not a mandatory dependency): Rustenwer produces
  a model or policy-compatible architecture → Syrius improves its behavior
  inside an environment through RL → Syrius produces a checkpoint and
  evaluation results → Rustenwer packages or optimizes the resulting model
  for inference → Polygrow registers and orchestrates the resulting
  intelligence artifact. A workflow may equally start in Syrius or use
  only Rustenwer.
- Neither project imports the other's internal implementation. Composition
  happens through explicit artifacts, APIs, or orchestration contracts
  (see below).

## What must not be duplicated

Do not build a second copy of anything Polygrow owns: compute-provider
management, general-purpose remote job infrastructure, provider credential
management, generic GPU scheduling, shared usage/billing infrastructure,
generic artifact lifecycle infrastructure, general-purpose model/compute
orchestration. When Polygrow provides a capability, integrate with it
instead of recreating it. Do not assume Polygrow's implementation is
automatically better — consolidate by demonstrated equivalence, and keep
Syrius's stronger domain behavior behind an adapter.

## How Syrius is expected to integrate with Polygrow

1. **Contract first.** Stable domain verbs, defined around intent, not
   Modal details: `environment_simulation`, `rollout_generation`,
   `policy_training`, `policy_evaluation`, `rl_experiment`. A workload
   specification carries domain operation, input artifact references,
   immutable configuration, required runtime profile, timeout/resource
   constraints, output expectations, and reproducibility metadata — never
   raw Modal SDK parameters. The existing 71-tool registry
   (`GET /capabilities/tools`, `POST /capabilities/tools/{name}/run`) is
   the natural contract surface — but see point 4 on the sync/async gap.
2. **Compute interface.** Polygrow requests a specialized operation →
   Syrius validates it, defines environments and algorithms, produces a
   workload specification → Polygrow's compute interface validates,
   authorizes, budgets, selects a runtime profile, executes via the Modal
   adapter → a normalized job result returns → Syrius interprets it.
   Supported operations: submit a workload, inspect status, retrieve
   logs/progress, request cancellation, retrieve output artifact
   references, inspect execution metadata.
3. **Transitional adapter (Phase S2).** While Polygrow's compute interface
   is not ready, a small, isolated, explicitly transitional Modal adapter
   may live in this repo behind the worker/executor boundary, using the
   same workload contract where practical. It must be replaceable by
   Polygrow's managed interface without rewriting domain logic. Known
   rework, not small: the executor always uses `LocalStorage()` with
   `local://` URIs, and evaluation/export/history/download all read from
   local disk — a remote storage backend must replace `local://`
   everywhere at once, and the single-checkpoint/CPU assumptions baked
   into the data model (one `final_model.zip`, "latest by step",
   `training_engine: "stable-baselines3 PPO (CPU)"`) change with remote
   execution.
4. **Async by default.** The tool-dispatch endpoint
   (`POST /capabilities/tools/{name}/run`) runs handlers synchronously in
   the request today — including export via a `_FakeJob` that bypasses the
   queue. Any Polygrow-facing contract must be async (202 + job id, like
   the train/baseline/evaluate/export endpoints), with a compatibility
   adapter for existing sync callers. Do not expose the sync path as the
   RL contract.
5. **Lowest-friction first integration: MCP.** Expose the §4 verbs as an
   MCP server; Polygrow's existing outbound MCP client
   (`capability_engine/self_provider/`) consumes it through the
   `CapabilityRegistry` with no new plumbing. The HTTP API remains the
   fallback path.
6. **Compatibility first.** Adapters around existing behavior; old and new
   paths run in tests; the new path lands behind a feature flag or explicit
   configuration; the old path is deprecated only after equivalence on real
   representative workloads; every migration keeps a rollback path. Do not
   replace Polygrow's current model-production workflows — integrate as
   optional, explicitly selected production strategies.
7. **Provider execution success ≠ learning success.** A completed Modal
   job is not an improved policy. Syrius's independent evaluation stays
   the arbiter of quality.

## Current implementation status and known limitations

- **Status:** audit complete (S0, 2026-11-19 — see `cross-system-report.md`).
  No Modal code, no remote-provider code of any kind, no auth, no Polygrow
  integration surface. Phases S1–S4 are open work, gated on Roger's
  decisions (see the report §12, especially the Modal account and the
  auth/tenancy question).
- **Known limitations (pre-existing, unchanged by this doc):** no auth, no
  tenancy; local-filesystem coupling is load-bearing; single checkpoint per
  run, no promotion/rollback; no training resume, no hyperparameter search,
  no scenario comparison; no job logs/resource-usage endpoint; `env_version`
  hardcoded `1` in export; worker Dockerfile CMD is stale (Phase-0
  one-shot `heartbeat`, not the `run` loop); `S3Storage` exists but is
  unwired and untested; LangGraph 0.6.8 has 11 known vulnerabilities
  (fix = 1.x upgrade, separate work).
- **Tests at audit:** API 37/37, worker 4/4, web Vitest 30/30, `ruff` clean.

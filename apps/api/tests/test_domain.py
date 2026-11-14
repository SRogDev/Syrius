"""Tests: core domain models + job queue + capabilities + storage."""

import pytest
from syrius_api import jobs as queue
from syrius_api.capabilities import (
    CapabilityExecutionContext,
    EngineeringCapability,
    is_paid_compute,
    requires_human_approval,
)
from syrius_api.models import Environment, Experiment, Project
from syrius_api.storage import LocalStorage, S3Storage


def test_create_project_environment_experiment(session) -> None:
    project = Project(name="cartpole", description="slice")
    session.add(project)
    session.commit()
    env = Environment(project_id=project.id, name="cartpole", gym_id="CartPole-v1")
    session.add(env)
    session.commit()
    exp = Experiment(
        project_id=project.id, environment_id=env.id, name="ppo-1", config={"seed": 42}
    )
    session.add(exp)
    session.commit()
    assert session.get(Project, project.id).name == "cartpole"
    assert session.get(Experiment, exp.id).config["seed"] == 42


def test_job_queue_claim_complete_retry_cancel(session) -> None:
    job = queue.enqueue(session, kind="baseline", payload={"a": 1})
    assert job.status == "queued"
    claimed = queue.claim_job(session, worker_name="w1")
    assert claimed is not None and claimed.id == job.id
    assert claimed.status == "running"
    assert queue.claim_job(session, worker_name="w2") is None
    assert queue.heartbeat_job(session, job_id=job.id, worker_name="w1") is True
    queue.append_job_log(session, job_id=job.id, message="hello")
    done = queue.complete_job(session, job_id=job.id, result={"mean_reward": 10.0})
    assert done.status == "completed"
    assert done.result["mean_reward"] == 10.0

    failing = queue.enqueue(session, kind="train", payload={}, max_retries=1)
    queue.claim_job(session, worker_name="w1")
    again = queue.fail_job(session, job_id=failing.id, error="boom")
    assert again.status == "queued"  # one retry remains
    assert again.retry_count == 1
    queue.claim_job(session, worker_name="w1")
    terminal = queue.fail_job(session, job_id=failing.id, error="boom again")
    assert terminal.status == "failed"

    cancellable = queue.enqueue(session, kind="export", payload={})
    queue.cancel_job(session, job_id=cancellable.id)
    assert queue.job_is_cancelled(session, job_id=cancellable.id)


def test_capability_validation_permissions_limits() -> None:
    cap = EngineeringCapability(
        id="cap-1",
        name="train",
        input_schema={
            "type": "object",
            "properties": {"steps": {"type": "integer", "minimum": 1}},
            "required": ["steps"],
        },
        output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
        permissions=["training.run"],
        resource_limits={"total_timesteps": 20000},
    )
    assert cap.validate_input({"steps": 100}) == []
    assert cap.validate_input({})  # missing required
    assert cap.validate_input({"steps": 0})  # below minimum
    assert cap.validate_output({"ok": True}) == []
    ctx = CapabilityExecutionContext(actor="worker", permissions=["training.run"])
    assert cap.check_permissions(ctx) == []
    assert cap.check_permissions(CapabilityExecutionContext(actor="x")) == ["training.run"]
    assert cap.check_resource_limits({"total_timesteps": 20001})
    assert cap.check_resource_limits({"total_timesteps": 20000}) == []


def test_approval_gates() -> None:
    assert requires_human_approval("deploy_policy_to_production")
    assert not requires_human_approval("train_policy")
    assert is_paid_compute("spend_paid_compute")
    assert not is_paid_compute("train_policy")


def test_local_storage_roundtrip_and_traversal_guard(tmp_path) -> None:
    storage = LocalStorage(tmp_path / "store")
    uri = storage.put("a/b.json", b'{"x": 1}')
    assert uri == "local://a/b.json"
    assert storage.get("a/b.json") == b'{"x": 1}'
    assert storage.exists("a/b.json")
    storage.put_json("c.json", {"y": 2})
    assert storage.get_json("c.json") == {"y": 2}
    try:
        storage.put("../escape.txt", b"x")
    except ValueError:
        pass
    else:
        raise AssertionError("path traversal was not rejected")


def test_s3_storage_without_boto3_or_bucket_raises() -> None:
    try:
        import boto3  # noqa: F401
    except ImportError:
        try:
            S3Storage("some-bucket")
        except NotImplementedError:
            return
        raise AssertionError("S3Storage should raise without boto3")
    else:
        pytest.skip("boto3 is installed; S3 path is operator-configured")
        return

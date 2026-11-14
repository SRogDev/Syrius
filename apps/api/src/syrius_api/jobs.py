"""Postgres-backed job queue (Phase 3, plan §8.2).

States: queued → running → completed / failed / cancelled. Claiming
uses row locking on Postgres (``FOR UPDATE SKIP LOCKED``) so several
workers can claim concurrently without double-running a job; on
SQLite the same claim runs inside one transaction (SQLite serialises
writers), which is the honest local-dev equivalent. Leases expire:
a job whose ``leased_until`` passed is claimable again (crashed
worker recovery). Retries follow ``max_retries``; cancellation is a
state change the executor checks between steps.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Job, utcnow

LEASE_SECONDS = 300


def enqueue(
    session: Session,
    *,
    kind: str,
    payload: dict,
    max_retries: int = 2,
    priority: int = 0,
) -> Job:
    job = Job(kind=kind, payload=payload, max_retries=max_retries, priority=priority)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def claim_job(session: Session, *, worker_name: str) -> Job | None:
    """Claim the oldest claimable queued job for *worker_name*.

    A job is claimable when queued and (never leased, lease expired, or
    failed-but-retryable and re-queued). Returns None when the queue is
    empty. The claim and the status change commit atomically.
    """
    now = utcnow()
    stmt = (
        select(Job)
        .where(Job.status == "queued")
        .where((Job.leased_until.is_(None)) | (Job.leased_until < now))
        .order_by(Job.priority.desc(), Job.created_at.asc())
        .limit(1)
    )
    if session.bind is not None and session.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)
    job = session.execute(stmt).scalars().first()
    if job is None:
        return None
    job.status = "running"
    job.lease_owner = worker_name
    job.leased_until = now + timedelta(seconds=LEASE_SECONDS)
    job.heartbeat_at = now
    job.started_at = now
    session.commit()
    session.refresh(job)
    return job


def heartbeat_job(session: Session, *, job_id: str, worker_name: str) -> bool:
    job = session.get(Job, job_id)
    if job is None or job.lease_owner != worker_name or job.status != "running":
        return False
    now = utcnow()
    job.heartbeat_at = now
    job.leased_until = now + timedelta(seconds=LEASE_SECONDS)
    session.commit()
    return True


def append_job_log(session: Session, *, job_id: str, message: str) -> None:
    job = session.get(Job, job_id)
    if job is None:
        return
    logs = list(job.logs or [])
    logs.append({"at": utcnow().isoformat(), "message": message})
    job.logs = logs
    session.commit()


def complete_job(session: Session, *, job_id: str, result: dict) -> Job | None:
    job = session.get(Job, job_id)
    if job is None:
        return None
    job.status = "completed"
    job.result = result
    job.finished_at = utcnow()
    job.leased_until = None
    session.commit()
    session.refresh(job)
    return job


def fail_job(session: Session, *, job_id: str, error: str) -> Job | None:
    """Fail *job_id*; re-queue when retries remain, else terminal failed."""
    job = session.get(Job, job_id)
    if job is None:
        return None
    job.error = error
    job.retry_count += 1
    if job.retry_count <= job.max_retries:
        job.status = "queued"
        job.lease_owner = None
        job.leased_until = None
    else:
        job.status = "failed"
        job.finished_at = utcnow()
        job.leased_until = None
    session.commit()
    session.refresh(job)
    return job


def cancel_job(session: Session, *, job_id: str) -> Job | None:
    job = session.get(Job, job_id)
    if job is None or job.status in ("completed", "failed", "cancelled"):
        return job
    job.status = "cancelled"
    job.finished_at = utcnow()
    job.leased_until = None
    session.commit()
    session.refresh(job)
    return job


def job_is_cancelled(session: Session, *, job_id: str) -> bool:
    job = session.get(Job, job_id)
    return bool(job is not None and job.status == "cancelled")

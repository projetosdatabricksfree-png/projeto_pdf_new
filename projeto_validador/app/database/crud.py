"""
CRUD operations for the Pre-Flight Validation System.

All functions are async and use SQLAlchemy 2.0+ idioms.
Implements upsert semantics for idempotency (Rule 4).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Event,
    Job,
    JobStatus,
    PerformanceMetric,
    RoutingLog,
    ValidationResult,
)

# Dialect-specific insert builders (Rule 4 — Idempotency via native upsert)
try:
    from sqlalchemy.dialects.postgresql import insert as _pg_insert
except ImportError:  # pragma: no cover
    _pg_insert = None  # type: ignore[assignment]

from sqlalchemy.dialects.sqlite import insert as _sqlite_insert


# ─── Job CRUD ─────────────────────────────────────────────────────────────────

async def create_job(
    db: AsyncSession,
    *,
    job_id: str,
    original_filename: str,
    file_path: str,
    file_size_bytes: int,
    client_locale: str = "pt-BR",
) -> Job:
    """Create a new validation job with status QUEUED."""
    job = Job(
        id=job_id,
        original_filename=original_filename,
        file_path=file_path,
        file_size_bytes=file_size_bytes,
        status=JobStatus.QUEUED.value,
        client_locale=client_locale,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()
    return job


async def get_job(db: AsyncSession, job_id: str) -> Optional[Job]:
    """Retrieve a job by ID."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    return result.scalar_one_or_none()


async def update_job_status(
    db: AsyncSession,
    job_id: str,
    status: str,
) -> None:
    """Update the pipeline status of a job."""
    await db.execute(
        update(Job).where(Job.id == job_id).values(status=status)
    )
    await db.flush()


async def complete_job(
    db: AsyncSession,
    job_id: str,
    *,
    final_status: str,
    error_count: int,
    warning_count: int,
    detected_product: Optional[str] = None,
    processing_agent: Optional[str] = None,
) -> None:
    """Mark a job as DONE with its final verdict."""
    now = datetime.now(timezone.utc)
    job = await get_job(db, job_id)
    if job is None:
        return

    duration_ms: Optional[int] = None
    if job.submitted_at:
        submitted = job.submitted_at
        if submitted.tzinfo is None:
            submitted = submitted.replace(tzinfo=timezone.utc)
        duration_ms = int((now - submitted).total_seconds() * 1000)

    await db.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(
            status=JobStatus.DONE.value,
            final_status=final_status,
            completed_at=now,
            total_duration_ms=duration_ms,
            error_count=error_count,
            warning_count=warning_count,
            detected_product=detected_product,
            processing_agent=processing_agent,
        )
    )
    await db.flush()


async def fail_job(db: AsyncSession, job_id: str, reason: str) -> None:
    """Mark a job as FAILED."""
    now = datetime.now(timezone.utc)
    await db.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(
            status=JobStatus.FAILED.value,
            completed_at=now,
        )
    )
    await create_event(
        db,
        job_id=job_id,
        agent_name="system",
        event_type="ERROR",
        event_level="CRITICAL",
        payload=json.dumps({"reason": reason}),
    )
    await db.flush()


# ─── Event CRUD ───────────────────────────────────────────────────────────────

async def create_event(
    db: AsyncSession,
    *,
    job_id: str,
    agent_name: str,
    event_type: str,
    event_level: str = "INFO",
    payload: Optional[str] = None,
    duration_ms: Optional[int] = None,
) -> Event:
    """Log an audit event."""
    event = Event(
        job_id=job_id,
        agent_name=agent_name,
        event_type=event_type,
        event_level=event_level,
        payload=payload,
        duration_ms=duration_ms,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.flush()
    return event


# ─── Routing Log CRUD ────────────────────────────────────────────────────────

async def create_routing_log(
    db: AsyncSession,
    *,
    job_id: str,
    agent_origin: str,
    route_to: str,
    confidence: float,
    reason: str,
    metadata_snapshot: dict,
) -> RoutingLog:
    """Record a routing decision."""
    log = RoutingLog(
        job_id=job_id,
        agent_origin=agent_origin,
        route_to=route_to,
        confidence=confidence,
        reason=reason,
        metadata_snapshot=json.dumps(metadata_snapshot),
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.flush()
    return log


# ─── Validation Result CRUD (with upsert for idempotency) ────────────────────

async def upsert_validation_result(
    db: AsyncSession,
    *,
    job_id: str,
    agent_name: str,
    check_code: str,
    check_name: str,
    status: str,
    error_code: Optional[str] = None,
    value_found: Optional[str] = None,
    value_expected: Optional[str] = None,
    pages_affected: Optional[list[int]] = None,
) -> None:
    """Insert or update a validation result (idempotent by job_id + check_code).

    Detects the database dialect at runtime and executes the appropriate
    native ON CONFLICT DO UPDATE statement, eliminating the SELECT + INSERT/UPDATE
    race condition present in the previous implementation (Rule 4 — Idempotency).

    Requires a UniqueConstraint on (job_id, check_code) in the ValidationResult
    model — see models.py uq_validation_result_job_check.
    """
    from app.database.session import engine

    pages_json = json.dumps(pages_affected) if pages_affected else None
    now = datetime.now(timezone.utc)

    insert_values: dict = {
        "job_id": job_id,
        "agent_name": agent_name,
        "check_code": check_code,
        "check_name": check_name,
        "status": status,
        "error_code": error_code,
        "value_found": value_found,
        "value_expected": value_expected,
        "pages_affected": pages_json,
        "timestamp": now,
    }
    # Columns to overwrite on conflict (exclude the natural key columns)
    update_values: dict = {
        k: v for k, v in insert_values.items() if k not in ("job_id", "check_code")
    }

    dialect_name: str = engine.dialect.name  # 'sqlite' | 'postgresql'

    if dialect_name == "postgresql" and _pg_insert is not None:
        stmt = (
            _pg_insert(ValidationResult)
            .values(**insert_values)
            .on_conflict_do_update(
                constraint="uq_validation_result_job_check",
                set_=update_values,
            )
        )
    else:
        # SQLite (default for dev) — also the safe fallback for any other dialect
        stmt = (
            _sqlite_insert(ValidationResult)
            .values(**insert_values)
            .on_conflict_do_update(
                index_elements=["job_id", "check_code"],
                set_=update_values,
            )
        )

    await db.execute(stmt)
    await db.flush()


# ─── Performance Metric CRUD ─────────────────────────────────────────────────

async def create_performance_metric(
    db: AsyncSession,
    *,
    job_id: str,
    stage: str,
    agent_name: str,
    start_time: datetime,
    end_time: Optional[datetime] = None,
    duration_ms: Optional[int] = None,
    file_size_bytes: Optional[int] = None,
    memory_peak_mb: Optional[float] = None,
) -> PerformanceMetric:
    """Record a performance metric for a pipeline stage."""
    metric = PerformanceMetric(
        job_id=job_id,
        stage=stage,
        agent_name=agent_name,
        start_time=start_time,
        end_time=end_time,
        duration_ms=duration_ms,
        file_size_bytes=file_size_bytes,
        memory_peak_mb=memory_peak_mb,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(metric)
    await db.flush()
    return metric


# ─── Query Helpers ────────────────────────────────────────────────────────────

async def get_job_events(db: AsyncSession, job_id: str) -> list[Event]:
    """Retrieve all events for a job, ordered by timestamp."""
    result = await db.execute(
        select(Event)
        .where(Event.job_id == job_id)
        .order_by(Event.timestamp)
    )
    return list(result.scalars().all())


async def get_job_validation_results(
    db: AsyncSession, job_id: str
) -> list[ValidationResult]:
    """Retrieve all validation results for a job."""
    result = await db.execute(
        select(ValidationResult)
        .where(ValidationResult.job_id == job_id)
        .order_by(ValidationResult.check_code)
    )
    return list(result.scalars().all())

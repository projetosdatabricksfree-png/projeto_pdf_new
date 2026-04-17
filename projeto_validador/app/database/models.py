"""
SQLAlchemy 2.0+ async models for the Pre-Flight Validation System.

Models: Job, Event, RoutingLog, ValidationResult, PerformanceMetric
All fields match exactly the specification in PROMPT_IMPLEMENTACAO.md.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ─── Auth Models ──────────────────────────────────────────────────────────────

class User(Base):
    """System user for authentication."""
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    email: str = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password: str = Column(String(255), nullable=False)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, nullable=False, default=func.now())


# ─── Enums ────────────────────────────────────────────────────────────────────

class JobStatus(str, enum.Enum):
    """Pipeline status for a job."""
    QUEUED = "QUEUED"
    ROUTING = "ROUTING"
    PROCESSING = "PROCESSING"
    VALIDATING = "VALIDATING"
    DONE = "DONE"
    FAILED = "FAILED"


class FinalStatus(str, enum.Enum):
    """Final validation verdict."""
    APROVADO = "APROVADO"
    REPROVADO = "REPROVADO"
    APROVADO_COM_RESSALVAS = "APROVADO_COM_RESSALVAS"


class EventType(str, enum.Enum):
    """Types of system events."""
    STATUS_CHANGE = "STATUS_CHANGE"
    ROUTING = "ROUTING"
    VALIDATION = "VALIDATION"
    ERROR = "ERROR"
    INFO = "INFO"
    SLA_VIOLATION = "SLA_VIOLATION"


class EventLevel(str, enum.Enum):
    """Severity levels for events."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CheckStatus(str, enum.Enum):
    """Status of an individual validation check."""
    OK = "OK"
    ERRO = "ERRO"
    AVISO = "AVISO"
    NA = "N/A"


# ─── Models ───────────────────────────────────────────────────────────────────

class Job(Base):
    """Represents a validation job submitted by the client."""
    __tablename__ = "jobs"

    id: str = Column(String(36), primary_key=True)  # UUID4
    original_filename: str = Column(String(512), nullable=False)
    file_path: str = Column(String(1024), nullable=False)
    file_size_bytes: int = Column(Integer, nullable=False, default=0)
    status: str = Column(
        String(20),
        nullable=False,
        default=JobStatus.QUEUED.value,
    )
    final_status: Optional[str] = Column(String(30), nullable=True)
    client_locale: str = Column(String(10), nullable=False, default="pt-BR")
    submitted_at: datetime = Column(DateTime, nullable=False, default=func.now())
    completed_at: Optional[datetime] = Column(DateTime, nullable=True)
    total_duration_ms: Optional[int] = Column(Integer, nullable=True)
    error_count: int = Column(Integer, nullable=False, default=0)
    warning_count: int = Column(Integer, nullable=False, default=0)
    detected_product: Optional[str] = Column(String(200), nullable=True)
    processing_agent: Optional[str] = Column(String(100), nullable=True)
    verapdf_report: Optional[str] = Column(Text, nullable=True)  # Sprint C: JSON VeraPDFReport

    # Relationships
    events = relationship("Event", back_populates="job", lazy="selectin")
    routing_logs = relationship("RoutingLog", back_populates="job", lazy="selectin")
    validation_results = relationship(
        "ValidationResult", back_populates="job", lazy="selectin"
    )
    performance_metrics = relationship(
        "PerformanceMetric", back_populates="job", lazy="selectin"
    )


class Event(Base):
    """Audit event logged by any agent."""
    __tablename__ = "events"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    job_id: str = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    agent_name: str = Column(String(100), nullable=False)
    event_type: str = Column(String(30), nullable=False)
    event_level: str = Column(String(10), nullable=False, default=EventLevel.INFO.value)
    payload: Optional[str] = Column(Text, nullable=True)  # JSON serialized
    duration_ms: Optional[int] = Column(Integer, nullable=True)
    timestamp: datetime = Column(DateTime, nullable=False, default=func.now())

    job = relationship("Job", back_populates="events")


class RoutingLog(Base):
    """Records routing decisions made by Gerente or Especialista."""
    __tablename__ = "routing_log"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    job_id: str = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    agent_origin: str = Column(String(50), nullable=False)  # gerente | especialista
    route_to: str = Column(String(100), nullable=False)
    confidence: float = Column(Float, nullable=False, default=0.0)
    reason: str = Column(String(255), nullable=True)
    metadata_snapshot: Optional[str] = Column(Text, nullable=True)  # JSON
    timestamp: datetime = Column(DateTime, nullable=False, default=func.now())

    job = relationship("Job", back_populates="routing_logs")


class ValidationResult(Base):
    """Individual validation check result from an Operário."""
    __tablename__ = "validation_results"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    job_id: str = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    agent_name: str = Column(String(100), nullable=False)
    check_code: str = Column(String(20), nullable=False)  # V01, V02...
    check_name: str = Column(String(100), nullable=False)
    status: str = Column(String(10), nullable=False)  # OK | ERRO | AVISO | N/A
    error_code: Optional[str] = Column(String(50), nullable=True)  # E001_..., W001_...
    value_found: Optional[str] = Column(String(255), nullable=True)
    value_expected: Optional[str] = Column(String(255), nullable=True)
    pages_affected: Optional[str] = Column(Text, nullable=True)  # JSON array
    timestamp: datetime = Column(DateTime, nullable=False, default=func.now())

    # Unique constraint required for idempotent ON CONFLICT upserts (Rule 4)
    __table_args__ = (
        UniqueConstraint("job_id", "check_code", name="uq_validation_result_job_check"),
    )

    job = relationship("Job", back_populates="validation_results")


class PerformanceMetric(Base):
    """Performance metrics for each pipeline stage."""
    __tablename__ = "performance_metrics"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    job_id: str = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    stage: str = Column(String(20), nullable=False)  # INGEST | ROUTING | ...
    agent_name: str = Column(String(100), nullable=False)
    start_time: datetime = Column(DateTime, nullable=False)
    end_time: Optional[datetime] = Column(DateTime, nullable=True)
    duration_ms: Optional[int] = Column(Integer, nullable=True)
    file_size_bytes: Optional[int] = Column(Integer, nullable=True)
    memory_peak_mb: Optional[float] = Column(Float, nullable=True)
    timestamp: datetime = Column(DateTime, nullable=False, default=func.now())

    job = relationship("Job", back_populates="performance_metrics")

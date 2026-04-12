"""
Pydantic schemas for inter-agent communication.

These are the mandatory payloads used across the pipeline.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─── Diretor → Gerente (queue:jobs) ───────────────────────────────────────────

class JobPayload(BaseModel):
    """Payload published to queue:jobs after file upload."""
    job_id: str
    file_path: str
    original_filename: str
    file_size_bytes: int
    submitted_at: datetime
    client_locale: str = "pt-BR"


# ─── Gerente/Especialista → Operário (queue:operario_*) ──────────────────────

class RoutingPayload(BaseModel):
    """Payload published after routing decision."""
    job_id: str
    file_path: str
    file_size_bytes: int
    route_to: str
    confidence: float
    reason: str
    metadata_snapshot: dict = {}
    client_locale: str = "pt-BR"
    job_metadata: dict = {}  # gramatura, encadernação, etc.


# ─── Operário → Validador (queue:validador) ──────────────────────────────────

class TechnicalReport(BaseModel):
    """Technical report produced by an Operário."""
    job_id: str
    agent: str
    produto_detectado: str
    status: str  # computed by operário
    erros_criticos: list[str] = []
    avisos: list[str] = []
    validation_results: dict[str, dict] = {}
    processing_time_ms: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    dimensoes_mm: Optional[dict] = None
    paginas_com_erro: list[int] = []


# ─── Validador → Cliente (GET /jobs/{id}/report) ─────────────────────────────

class FinalReport(BaseModel):
    """Final report returned to the client."""
    job_id: str
    status: str  # APROVADO | REPROVADO | APROVADO_COM_RESSALVAS
    produto: str
    agente_processador: Optional[str] = None
    avaliado_em: datetime
    tempo_processamento_ms: int = 0
    resumo: str
    erros: list[dict] = []
    avisos: list[dict] = []
    detalhes_tecnicos: dict = {}


# ─── API Response Schemas ────────────────────────────────────────────────────

class JobCreatedResponse(BaseModel):
    """Response for POST /api/v1/validate."""
    job_id: str
    status: str = "QUEUED"
    polling_url: str
    message: str = "Arquivo recebido. Validação em andamento."


class JobStatusResponse(BaseModel):
    """Response for GET /api/v1/jobs/{job_id}/status."""
    job_id: str
    status: str
    final_status: Optional[str] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_ms: Optional[int] = None
    error_count: int = 0
    warning_count: int = 0


class HealthResponse(BaseModel):
    """Response for GET /api/v1/health."""
    status: str = "healthy"
    service: str = "preflight-validator"
    version: str = "1.0.0"


# ─── Audit Event Payload ─────────────────────────────────────────────────────

class AuditEvent(BaseModel):
    """Payload published to queue:audit by all agents."""
    job_id: str
    agent_name: str
    event_type: str
    event_level: str = "INFO"
    payload: dict = {}
    duration_ms: Optional[int] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now())

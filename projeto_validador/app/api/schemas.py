"""
Pydantic schemas for inter-agent communication.

These are the mandatory payloads used across the pipeline.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# ─── Diretor → Gerente (queue:jobs) ───────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


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
    produto_detectado: Optional[str] = None


# ─── Operário → Validador (queue:validador) ──────────────────────────────────

class ValidationResult(BaseModel):
    """Standard audit result for a single validation check."""
    status: str  # OK | REPROVADO | AVISO
    codigo: Optional[str] = None
    label: Optional[str] = None
    found_value: Optional[str] = None
    expected_value: Optional[str] = None
    paginas: list[int] = []
    meta: dict = {}

class TechnicalReport(BaseModel):
    """Technical report produced by an Operário."""
    job_id: str
    agent: str
    produto_detectado: str
    status: str  # computed by operário
    erros_criticos: list[str] = []
    avisos: list[str] = []
    validation_results: dict[str, ValidationResult] = {}
    processing_time_ms: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    dimensoes_mm: Optional[dict] = None
    paginas_com_erro: list[int] = []
    file_path: Optional[str] = None  # forwarded so Gold layer can locate Bronze PDF


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


# ─── Gold Layer: Remediation + Final Validation ──────────────────────────────

class RemediationAction(BaseModel):
    """Outcome of one Remediator invocation against a specific error.

    Contract (post-Sprint A):
    - success=True  → operation completed; degradations go in quality_loss_warnings
    - success=False → technical failure only (binary missing, timeout, unhandled crash)
    """
    codigo: str
    remediator: str
    success: bool
    changes_applied: list[str] = []
    quality_loss_warnings: list[str] = []
    quality_loss_severity: str = "none"  # none | low | medium | high
    technical_log: str = ""


class RemediationReport(BaseModel):
    """Aggregate report produced by the remediation orchestrator."""
    job_id: str
    input_path: str          # Bronze (original)
    output_path: str         # Gold candidate (_gold.pdf)
    actions: list[RemediationAction] = []
    overall_success: bool = False
    pdfx_version_target: str = "PDF/X-4"
    icc_profile: str = "ISOcoated_v2_300_eci.icc"
    timestamp: datetime = Field(default_factory=lambda: datetime.now())


class GoldValidationReport(BaseModel):
    """Final verdict from validador_final — only is_gold=True ships to production."""
    job_id: str
    is_gold: bool
    pdfx_compliance: dict = {}     # {version, gts_pdfx_version, output_intent}
    remaining_errors: list[ValidationResult] = []
    rejection_reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now())


# ─── Sprint C: VeraPDF Attestation ──────────────────────────────────────────

class VeraPDFRuleViolation(BaseModel):
    """A single rule violation from VeraPDF output."""
    rule_id: str
    object_type: str = ""
    description: str = ""
    check_count: int = 0
    failed_count: int = 0
    passed_count: int = 0


class VeraPDFReport(BaseModel):
    """Structured output from the VeraPDF CLI audit.

    Persisted as JSON in tmp/gold/{job_id}_verapdf.json and in jobs.verapdf_report.
    """
    job_id: str
    passed: bool
    profile: str = "PDF/X-4"
    rule_violations: list[VeraPDFRuleViolation] = []
    raw_json: str = ""
    gold_path: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now())


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

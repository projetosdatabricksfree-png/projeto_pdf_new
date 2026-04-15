"""
Validador Final — the 'cliente final' gate.

Runs the full GWG inspector suite against a remediated PDF. Only emits
is_gold=True when: (a) no critical errors remain, and (b) the file exhibits
structural PDF/X-4 conformance (GTS_PDFXVersion + CMYK OutputIntent).

This agent does not 'correct' — rejection here is final. The RemediationReport
is attached to the audit trail so a human can see why the job didn't graduate
from Silver to Gold.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.api.schemas import GoldValidationReport, ValidationResult

from .pdfx_compliance import check_pdfx4

logger = logging.getLogger(__name__)


def validate_gold(job_id: str, pdf_path: Path) -> GoldValidationReport:
    """Inspect a Gold candidate and return the final verdict."""
    from agentes.operarios.shared_tools.gwg.run_full_suite import run_all_gwg_checks

    pdfx = check_pdfx4(pdf_path)

    try:
        suite = run_all_gwg_checks(str(pdf_path), profile={}, job_id=job_id)
    except Exception as exc:
        logger.exception("validador_final suite crash: %s", exc)
        return GoldValidationReport(
            job_id=job_id,
            is_gold=False,
            pdfx_compliance=pdfx,
            rejection_reason=f"Inspector crash on Gold candidate: {exc}",
        )

    remaining: list[ValidationResult] = []
    for entry in suite.get("normalized", []):
        status = entry.get("status")
        if status in {"ERRO", "REPROVADO", "FAIL"}:
            remaining.append(
                ValidationResult(
                    status="REPROVADO",
                    codigo=entry.get("codigo"),
                    label=entry.get("label"),
                    found_value=entry.get("found_value"),
                    expected_value=entry.get("expected_value"),
                    paginas=entry.get("paginas", []) or [],
                    meta=entry.get("meta", {}) or {},
                )
            )

    is_gold = not remaining and pdfx["is_compliant"]
    reason: str | None = None
    if not is_gold:
        parts = []
        if remaining:
            codes = ", ".join(sorted({r.codigo for r in remaining if r.codigo}))
            parts.append(f"residual errors after remediation: {codes}")
        if not pdfx["is_compliant"]:
            parts.append(f"PDF/X-4 non-compliant: {'; '.join(pdfx['errors'])}")
        reason = " | ".join(parts)

    return GoldValidationReport(
        job_id=job_id,
        is_gold=is_gold,
        pdfx_compliance=pdfx,
        remaining_errors=remaining,
        rejection_reason=reason,
    )

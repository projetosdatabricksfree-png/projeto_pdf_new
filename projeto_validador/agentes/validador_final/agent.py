"""
Validador Final — audit layer for the Gold candidate.

Sprint C: consumes VeraPDFReport (authoritative PDF/X-4 verdict) instead of the
pragmatic check_pdfx4() heuristic. check_pdfx4() is kept as fallback when the
VeraPDF container is offline (AC3).

Post-Sprint A contract:
  is_gold=True  → no critical errors remain AND PDF/X-4 structurally compliant.
  is_gold=False → residual errors or non-compliance detected (file still ships).

Terminal statuses:
  GOLD_DELIVERED              → is_gold=True
  GOLD_DELIVERED_WITH_WARNINGS → is_gold=False (file still ships)

This agent audits only — it does not correct.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.api.schemas import GoldValidationReport, ValidationResult, VeraPDFReport

from .pdfx_compliance import check_pdfx4

logger = logging.getLogger(__name__)


def _verapdf_to_pdfx_compliance(report: VeraPDFReport) -> dict:
    """Convert a VeraPDFReport into the pdfx_compliance dict shape used by GoldValidationReport."""
    errors = [f"Rule {v.rule_id}: {v.description}" for v in report.rule_violations]
    return {
        "is_compliant": report.passed,
        "gts_pdfx_version": "PDF/X-4" if report.passed else None,
        "output_intent_subtype": "/GTS_PDFX" if report.passed else None,
        "output_intent_identifier": None,
        "has_output_profile": report.passed,
        "errors": errors,
        "source": "verapdf",
        "profile": report.profile,
    }


def try_verapdf_audit(pdf_path: Path) -> VeraPDFReport | None:
    """Run VeraPDF locally (synchronous convenience call).

    Used by validate_gold() when task_verapdf_audit is not pre-populated.
    Returns None if VeraPDF is unavailable (triggers fallback to check_pdfx4).
    """
    try:
        from workers.tasks_verapdf import _parse_verapdf_json, run_verapdf

        ok, stdout, stderr = run_verapdf(pdf_path)
        if not ok:
            logger.debug("[validador_final] VeraPDF unavailable: %s", stderr)
            return None

        parsed = _parse_verapdf_json(stdout, job_id="inline")
        return VeraPDFReport(
            job_id="inline",
            passed=parsed["passed"],
            profile=parsed.get("profile", "PDF/X-4"),
            rule_violations=parsed.get("rule_violations", []),
            raw_json=stdout,
            gold_path=str(pdf_path),
        )
    except Exception as exc:
        logger.debug("[validador_final] VeraPDF probe failed: %s", exc)
        return None


def validate_gold(
    job_id: str,
    pdf_path: Path,
    verapdf_report: VeraPDFReport | None = None,
) -> GoldValidationReport:
    """Inspect a Gold candidate and return the final verdict.

    Args:
        job_id: Pipeline job identifier.
        pdf_path: Path to the _gold.pdf file.
        verapdf_report: Pre-computed VeraPDFReport from task_verapdf_audit.
            If None, attempts to run VeraPDF inline; falls back to check_pdfx4.
    """
    from agentes.operarios.shared_tools.gwg.run_full_suite import run_all_gwg_checks

    # ── PDF/X-4 compliance: VeraPDF (authoritative) or fallback ──────────────
    if verapdf_report is None:
        verapdf_report = try_verapdf_audit(pdf_path)

    if verapdf_report is not None:
        # AC1: use VeraPDF result
        pdfx = _verapdf_to_pdfx_compliance(verapdf_report)
        # AC2: is_gold driven by verapdf.passed
        verapdf_passed = verapdf_report.passed
        logger.info(
            "[validador_final] VeraPDF audit: job=%s passed=%s violations=%d",
            job_id, verapdf_passed, len(verapdf_report.rule_violations),
        )
    else:
        # AC3: VeraPDF offline — fall back to pragmatic check, emit warning
        logger.warning(
            "[validador_final] VeraPDF unavailable for job %s — falling back to check_pdfx4()",
            job_id,
        )
        pdfx = check_pdfx4(pdf_path)
        pdfx["source"] = "fallback_pdfx_compliance"
        verapdf_passed = pdfx["is_compliant"]

    # ── GWG suite for residual structural errors ──────────────────────────────
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

    is_gold = not remaining and verapdf_passed
    reason: str | None = None
    if not is_gold:
        parts = []
        if remaining:
            codes = ", ".join(sorted({r.codigo for r in remaining if r.codigo}))
            parts.append(f"residual errors after remediation: {codes}")
        if not verapdf_passed:
            src = pdfx.get("source", "verapdf")
            errs = pdfx.get("errors", [])
            parts.append(f"PDF/X-4 non-compliant [{src}]: {'; '.join(errs)}")
        reason = " | ".join(parts)

    return GoldValidationReport(
        job_id=job_id,
        is_gold=is_gold,
        pdfx_compliance=pdfx,
        remaining_errors=remaining,
        rejection_reason=reason,
    )

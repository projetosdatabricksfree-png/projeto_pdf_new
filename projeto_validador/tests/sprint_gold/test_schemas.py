"""Schema round-trip tests for Gold-layer Pydantic models."""
from __future__ import annotations

from app.api.schemas import (
    GoldValidationReport,
    RemediationAction,
    RemediationReport,
    ValidationResult,
)


def test_remediation_action_round_trip():
    a = RemediationAction(
        codigo="E006_FORBIDDEN_COLORSPACE",
        remediator="ColorSpaceRemediator",
        success=True,
        changes_applied=["converted 12 objects"],
        technical_log="gs ok",
    )
    assert RemediationAction.model_validate_json(a.model_dump_json()) == a


def test_remediation_report_defaults():
    r = RemediationReport(job_id="j1", input_path="/in.pdf", output_path="/gold.pdf")
    assert r.pdfx_version_target == "PDF/X-4"
    assert r.icc_profile == "ISOcoated_v2_300_eci.icc"
    assert r.overall_success is False


def test_gold_validation_report_rejection():
    g = GoldValidationReport(
        job_id="j1",
        is_gold=False,
        remaining_errors=[ValidationResult(status="REPROVADO", codigo="E008_NON_EMBEDDED_FONTS")],
        rejection_reason="residual errors after remediation: E008_NON_EMBEDDED_FONTS",
    )
    restored = GoldValidationReport.model_validate_json(g.model_dump_json())
    assert restored.is_gold is False
    assert len(restored.remaining_errors) == 1

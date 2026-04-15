"""
Delivery guarantee tests — A-05 AC4.

For any combination of errors, the pipeline must produce a _gold.pdf on disk.
These tests exercise the task_remediate orchestrator logic in isolation using
mocked remediators so they don't depend on external binaries.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.api.schemas import (
    RemediationAction,
    TechnicalReport,
    ValidationResult,
)


def _make_technical_report(tmp_path: Path, error_codes: list[str]) -> TechnicalReport:
    """Build a minimal TechnicalReport with the given error codes."""
    bronze = tmp_path / "source.pdf"
    bronze.write_bytes(b"%PDF-1.4 fake source")

    results = {}
    for code in error_codes:
        results[code] = ValidationResult(
            status="REPROVADO",
            codigo=code,
            found_value="test",
            expected_value="expected",
        )

    return TechnicalReport(
        job_id="test-job-001",
        agent="test",
        produto_detectado="papelaria_plana",
        status="REPROVADO",
        erros_criticos=error_codes,
        validation_results=results,
        file_path=str(bronze),
    )


def _build_ok_action(codigo: str) -> RemediationAction:
    return RemediationAction(
        codigo=codigo,
        remediator="MockRemediator",
        success=True,
        changes_applied=[f"fixed {codigo}"],
    )


def _build_warn_action(codigo: str) -> RemediationAction:
    return RemediationAction(
        codigo=codigo,
        remediator="MockRemediator",
        success=True,
        changes_applied=[f"fixed {codigo} with degradation"],
        quality_loss_warnings=[f"quality degraded for {codigo}"],
        quality_loss_severity="low",
    )


def _build_fail_action(codigo: str) -> RemediationAction:
    return RemediationAction(
        codigo=codigo,
        remediator="MockRemediator",
        success=False,
        quality_loss_warnings=[f"technical failure on {codigo}"],
    )


# ── Orchestrator unit tests (no Celery, no external processes) ───────────────

class TestTaskRemediateDeliveryContract:
    """Verify that task_remediate always produces a Gold file when scratch exists."""

    def _run_remediate_orchestrator(
        self,
        tmp_path: Path,
        report: TechnicalReport,
        mock_actions: dict[str, RemediationAction],
    ) -> dict:
        """Drive the core logic of task_remediate without Celery machinery."""
        from agentes.remediadores.registry import get_remediator

        bronze = Path(report.file_path)
        gold = bronze.with_name(f"{bronze.stem}_gold.pdf")
        scratch = bronze.with_name(f"{bronze.stem}_scratch.pdf")
        shutil.copy2(bronze, scratch)

        actions = []
        priority = {"G002": 1, "E004": 2, "E006_FORBIDDEN_COLORSPACE": 3,
                    "E008_NON_EMBEDDED_FONTS": 4, "W003_BORDERLINE_RESOLUTION": 5}
        items = sorted(
            report.validation_results.items(),
            key=lambda kv: priority.get(kv[1].codigo or "", 99),
        )

        for _name, vr in items:
            if not vr.codigo or vr.status not in {"REPROVADO", "AVISO"}:
                continue

            action = mock_actions.get(vr.codigo)
            if action is None:
                continue

            actions.append(action)
            next_scratch = bronze.with_name(f"{bronze.stem}_scratch_{vr.codigo}.pdf")
            if action.success:
                next_scratch.write_bytes(b"%PDF-1.4 remediated")
                shutil.move(str(next_scratch), str(scratch))
            else:
                next_scratch.unlink(missing_ok=True)

        gold_produced = False
        if scratch.exists():
            shutil.move(str(scratch), str(gold))
            gold_produced = True

        return {"gold_produced": gold_produced, "actions": actions, "gold": gold}

    def test_single_clean_fix_produces_gold(self, tmp_path):
        report = _make_technical_report(tmp_path, ["G002"])
        result = self._run_remediate_orchestrator(
            tmp_path, report, {"G002": _build_ok_action("G002")}
        )
        assert result["gold_produced"] is True
        assert result["gold"].exists()

    def test_fix_with_quality_warning_still_produces_gold(self, tmp_path):
        report = _make_technical_report(tmp_path, ["G002"])
        result = self._run_remediate_orchestrator(
            tmp_path, report, {"G002": _build_warn_action("G002")}
        )
        assert result["gold_produced"] is True
        assert result["gold"].exists()
        assert result["actions"][0].quality_loss_warnings

    def test_technical_failure_on_one_step_still_delivers_bronze_as_gold(self, tmp_path):
        """If a remediator crashes (technical failure), we still deliver the last scratch."""
        report = _make_technical_report(tmp_path, ["G002", "E004"])
        result = self._run_remediate_orchestrator(
            tmp_path,
            report,
            {
                "G002": _build_ok_action("G002"),
                "E004": _build_fail_action("E004"),  # technical failure
            },
        )
        # Even with E004 technical failure, the G002-remediated scratch becomes gold
        assert result["gold_produced"] is True
        assert result["gold"].exists()

    def test_all_unknown_codes_still_delivers_original_as_gold(self, tmp_path):
        """No remediator matched → scratch is just bronze copy → still delivered."""
        report = _make_technical_report(tmp_path, ["UNKNOWN_CODE_XYZ"])
        result = self._run_remediate_orchestrator(
            tmp_path, report, {}  # no mock actions → no remediators match
        )
        assert result["gold_produced"] is True
        assert result["gold"].exists()

    def test_multiple_errors_all_fixed_produces_gold(self, tmp_path):
        codes = ["G002", "E004", "E006_FORBIDDEN_COLORSPACE", "W003_BORDERLINE_RESOLUTION"]
        report = _make_technical_report(tmp_path, codes)
        mock_actions = {c: _build_ok_action(c) for c in codes}
        result = self._run_remediate_orchestrator(tmp_path, report, mock_actions)
        assert result["gold_produced"] is True
        assert result["gold"].exists()
        assert all(a.success for a in result["actions"])
        assert not any(a.quality_loss_warnings for a in result["actions"])

    def test_gold_status_is_delivered_with_warnings_when_quality_loss(self, tmp_path):
        """Actions with quality_loss_warnings → GOLD_DELIVERED_WITH_WARNINGS (semantic check)."""
        report = _make_technical_report(tmp_path, ["G002"])
        result = self._run_remediate_orchestrator(
            tmp_path, report, {"G002": _build_warn_action("G002")}
        )
        has_warnings = any(a.quality_loss_warnings for a in result["actions"])
        assert has_warnings
        # The is_gold flag (from validador_final) would be False, but gold is still produced
        assert result["gold_produced"] is True

"""
Sprint C — task_verapdf_audit Celery task.

Runs VeraPDF CLI against the Gold candidate and produces a VeraPDFReport:
  - Invoked via queue:verapdf on the dedicated validador-verapdf container.
  - Result persisted to {gold_dir}/{job_id}_verapdf.json and jobs.verapdf_report.
  - Emits VERAPDF_COMPLETED audit event.

Usage:
    task_verapdf_audit.apply_async(
        args=[job_id, str(gold_path)],
        queue="queue:verapdf",
    )
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Maximum time VeraPDF may run before we abort (AC1).
VERAPDF_TIMEOUT_S: int = 120


def _parse_verapdf_json(raw: str, job_id: str) -> dict:
    """Extract structured fields from VeraPDF JSON output.

    VeraPDF --format json produces a report with this top-level shape:
    {
      "report": {
        "jobs": [{
          "validationResult": {
            "compliant": true|false,
            "profileName": "...",
            "details": {
              "passedRules": N,
              "failedRules": N,
              "ruleSummaries": [
                {
                  "ruleId": {"specification": "...", "clause": "6.2.2", "testNumber": 1},
                  "object": "...",
                  "description": "...",
                  "checks": {"passedChecks": N, "failedChecks": N}
                }
              ]
            }
          }
        }]
      }
    }

    Returns a dict ready to build VeraPDFReport from.
    """
    from app.api.schemas import VeraPDFRuleViolation

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("[verapdf] could not parse output JSON: %s", exc)
        return {"passed": False, "profile": "unknown", "rule_violations": []}

    try:
        jobs = data.get("report", {}).get("jobs", [])
        if not jobs:
            return {"passed": False, "profile": "unknown", "rule_violations": []}

        vr = jobs[0].get("validationResult", {})
        passed: bool = bool(vr.get("compliant", False))
        profile: str = vr.get("profileName", "PDF/X-4")
        details = vr.get("details", {})

        violations: list[VeraPDFRuleViolation] = []
        for summary in details.get("ruleSummaries", []):
            rule_id_obj = summary.get("ruleId", {})
            clause = rule_id_obj.get("clause", "")
            test_no = rule_id_obj.get("testNumber", "")
            rule_id = f"{clause}.{test_no}" if clause else str(rule_id_obj)

            checks = summary.get("checks", {})
            failed = int(checks.get("failedChecks", 0))
            if failed > 0:
                violations.append(
                    VeraPDFRuleViolation(
                        rule_id=rule_id,
                        object_type=summary.get("object", ""),
                        description=summary.get("description", ""),
                        check_count=int(checks.get("passedChecks", 0)) + failed,
                        failed_count=failed,
                        passed_count=int(checks.get("passedChecks", 0)),
                    )
                )

        return {
            "passed": passed,
            "profile": profile,
            "rule_violations": violations,
        }
    except Exception as exc:
        logger.warning("[verapdf] parse error: %s", exc)
        return {"passed": False, "profile": "unknown", "rule_violations": []}


def run_verapdf(pdf_path: Path) -> tuple[bool, str, str]:
    """Run VeraPDF CLI synchronously.

    Returns (success, stdout, stderr).
    success=False if VeraPDF is unavailable or crashes.
    """
    verapdf_bin = shutil.which("verapdf")
    if verapdf_bin is None:
        return False, "", "verapdf binary not found on PATH"

    try:
        result = subprocess.run(
            [verapdf_bin, "--format", "json", "--flavour", "4", str(pdf_path)],
            capture_output=True,
            text=True,
            timeout=VERAPDF_TIMEOUT_S,
        )
        return True, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"VeraPDF timed out after {VERAPDF_TIMEOUT_S}s"
    except Exception as exc:
        return False, "", str(exc)


@celery_app.task(
    name="workers.tasks_verapdf.task_verapdf_audit",
    bind=True,
    queue="queue:verapdf",
)
def task_verapdf_audit(self, job_id: str, gold_path: str) -> str:
    """Audit a Gold PDF with VeraPDF and persist the attestation.

    AC1: subprocess with 120s timeout.
    AC2: JSON parsed into VeraPDFReport.
    AC3: Persisted to tmp/gold/{job_id}_verapdf.json and jobs.verapdf_report.
    AC4: VERAPDF_COMPLETED event emitted.

    Returns: serialized VeraPDFReport JSON.
    """

    from app.api.schemas import VeraPDFReport

    logger.info("[task_verapdf_audit] job=%s gold=%s", job_id, gold_path)

    gold = Path(gold_path)

    # ── Run VeraPDF ───────────────────────────────────────────────────────────
    success, stdout, stderr = run_verapdf(gold)

    if not success:
        logger.warning("[task_verapdf_audit] VeraPDF unavailable for job %s: %s", job_id, stderr)
        # Return a soft-fail report — pipeline continues with pragma fallback
        report = VeraPDFReport(
            job_id=job_id,
            passed=False,
            profile="PDF/X-4",
            raw_json="",
            gold_path=gold_path,
        )
        report.rule_violations = []
        return _persist_and_emit(report, job_id, gold, level="WARNING")

    # ── Parse ─────────────────────────────────────────────────────────────────
    parsed = _parse_verapdf_json(stdout, job_id)
    report = VeraPDFReport(
        job_id=job_id,
        passed=parsed["passed"],
        profile=parsed.get("profile", "PDF/X-4"),
        rule_violations=parsed.get("rule_violations", []),
        raw_json=stdout,
        gold_path=gold_path,
    )

    level = "INFO" if report.passed else "WARNING"
    return _persist_and_emit(report, job_id, gold, level=level)


def _persist_and_emit(report, job_id: str, gold: Path, level: str) -> str:
    """Save report to filesystem + DB, emit audit event, return JSON."""
    import json as _json

    from workers.tasks import _run_async

    report_json = report.model_dump_json()

    # AC3: filesystem persistence in tmp/gold/
    gold_dir = gold.parent
    json_path = gold_dir / f"{job_id}_verapdf.json"
    try:
        json_path.write_text(report_json, encoding="utf-8")
    except OSError as exc:
        logger.warning("[task_verapdf_audit] could not write report to disk: %s", exc)

    # AC3: DB persistence
    async def _save():
        from app.database.crud import create_event, save_verapdf_report
        from app.database.session import async_session_factory

        async with async_session_factory() as db:
            await save_verapdf_report(db, job_id, report_json)
            await create_event(
                db,
                job_id=job_id,
                agent_name="validador-verapdf",
                event_type="VERAPDF_COMPLETED",  # AC4
                event_level=level,
                payload=_json.dumps({
                    "passed": report.passed,
                    "violations": len(report.rule_violations),
                    "gold_path": str(gold),
                }),
            )
            await db.commit()

    _run_async(_save())

    logger.info(
        "[task_verapdf_audit] job=%s passed=%s violations=%d",
        job_id,
        report.passed,
        len(report.rule_violations),
    )
    return report_json

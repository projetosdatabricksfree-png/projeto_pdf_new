"""
Sprint A Regression Stress Test — A-08.

Reads PDFs from tests/fixtures/real_batch/ (versioned batch) or falls back to
SOURCE_DIR_LEGACY if the fixture directory is empty.

Produces:
  - Console summary
  - docs/SPRINT_QA/AUTO_REMEDIATION/reports/sprint_a_batch.md  (A-08 AC2)

Exit criteria (A-08 AC3):
  ≥8/10 files with status GOLD_DELIVERED or GOLD_DELIVERED_WITH_WARNINGS
  AND _gold.pdf non-empty.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests

# ── Settings ─────────────────────────────────────────────────────────────────

API_URL = "http://localhost:8001/api/v1"
CONCURRENCY = 8  # matches number of workers

FIXTURE_BATCH_DIR = (
    Path(__file__).parent.parent / "tests" / "fixtures" / "real_batch"
)
SOURCE_DIR_LEGACY = "/home/diego/Documents"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "docs" / "SPRINT_QA" / "AUTO_REMEDIATION" / "reports"
REPORT_PATH = OUTPUT_DIR / "sprint_a_batch.md"

DELIVERED_STATUSES = {"GOLD_DELIVERED", "GOLD_DELIVERED_WITH_WARNINGS"}
# Backwards-compat: accept old status names during transition
DELIVERED_STATUSES_COMPAT = DELIVERED_STATUSES | {"GOLD_APPROVED"}
POLL_TIMEOUT_S = 300


# ── Processing ────────────────────────────────────────────────────────────────

def process_file(file_path: Path) -> dict:
    filename = file_path.name
    print(f"[START] {filename}")

    # 1. Upload
    try:
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{API_URL}/validate",
                files={"file": (filename, f, "application/pdf")},
                data={"client_locale": "pt-BR"},
                timeout=30,
            )
    except Exception as exc:
        return {"file": filename, "status": "UPLOAD_EXCEPTION", "error": str(exc)}

    if resp.status_code != 202:
        return {"file": filename, "status": "UPLOAD_FAILED", "error": resp.text[:200]}

    job_id = resp.json()["job_id"]
    print(f"[QUEUED] {filename} → job {job_id}")

    # 2. Poll for completion
    deadline = time.time() + POLL_TIMEOUT_S
    while True:
        if time.time() > deadline:
            return {
                "file": filename,
                "status": "TIMEOUT",
                "job_id": job_id,
                "error": f"Exceeded {POLL_TIMEOUT_S}s timeout",
            }
        try:
            status_resp = requests.get(f"{API_URL}/jobs/{job_id}/status", timeout=10)
        except Exception as exc:
            return {"file": filename, "status": "POLL_EXCEPTION", "job_id": job_id, "error": str(exc)}

        if status_resp.status_code != 200:
            return {"file": filename, "status": "POLL_FAILED", "job_id": job_id, "error": status_resp.text[:200]}

        data = status_resp.json()
        status = data["status"]

        terminal = (
            status in DELIVERED_STATUSES_COMPAT
            or status in {"GOLD_REJECTED", "FAILED", "DONE"}
        )
        if terminal:
            print(f"[DONE] {filename} → {status}")

            # 3. Download gold PDF
            gold_size: int | None = None
            gold_filename: str | None = None
            if status in DELIVERED_STATUSES_COMPAT:
                gold_resp = requests.get(f"{API_URL}/jobs/{job_id}/gold", timeout=30)
                if gold_resp.status_code == 200:
                    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                    gold_filename = f"{file_path.stem}_gold.pdf"
                    gold_path = OUTPUT_DIR / gold_filename
                    gold_path.write_bytes(gold_resp.content)
                    gold_size = len(gold_resp.content)
                else:
                    gold_filename = None

            # 4. Fetch warnings from report if available
            quality_warnings: list[str] = []
            try:
                report_resp = requests.get(f"{API_URL}/jobs/{job_id}/report", timeout=10)
                if report_resp.status_code == 200:
                    report_data = report_resp.json()
                    quality_warnings = report_data.get("quality_loss_warnings", [])
            except Exception:
                pass

            return {
                "file": filename,
                "status": status,
                "job_id": job_id,
                "gold_file": gold_filename,
                "gold_size_bytes": gold_size,
                "quality_warnings": quality_warnings,
            }

        time.sleep(2)


# ── Report generation ─────────────────────────────────────────────────────────

def write_report(results: list[dict], elapsed: float) -> None:
    delivered = [r for r in results if r["status"] in DELIVERED_STATUSES_COMPAT]
    delivered_with_gold = [
        r for r in delivered
        if r.get("gold_size_bytes") and r["gold_size_bytes"] > 0
    ]
    failed = [r for r in results if r["status"] not in DELIVERED_STATUSES_COMPAT]

    total = len(results)
    score = len(delivered_with_gold)
    goal_met = score >= 8 and total >= 10

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Sprint A Batch Stress Test Report",
        f"",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total files:** {total}",
        f"**Delivered (gold.pdf non-empty):** {score}/{total}",
        f"**Goal (≥8/10):** {'PASSED' if goal_met else 'FAILED'}",
        f"**Elapsed:** {elapsed:.1f}s",
        f"",
        f"---",
        f"",
        f"## Results by File",
        f"",
        f"| File | Status | gold.pdf size | Quality Warnings |",
        f"|---|---|---|---|",
    ]

    for r in sorted(results, key=lambda x: x["file"]):
        icon = "✅" if r["status"] in DELIVERED_STATUSES else "⚠️" if r["status"] in {"GOLD_APPROVED"} else "❌"
        size = f"{r.get('gold_size_bytes', 0):,} bytes" if r.get("gold_size_bytes") else "—"
        warnings = "; ".join(r.get("quality_warnings", [])[:2]) or "none"
        lines.append(f"| {icon} `{r['file']}` | `{r['status']}` | {size} | {warnings} |")

    lines += [
        f"",
        f"---",
        f"",
        f"## Summary",
        f"",
        f"- **Delivered clean** (`GOLD_DELIVERED`): {sum(1 for r in results if r['status'] == 'GOLD_DELIVERED')}",
        f"- **Delivered with warnings** (`GOLD_DELIVERED_WITH_WARNINGS`): {sum(1 for r in results if r['status'] == 'GOLD_DELIVERED_WITH_WARNINGS')}",
        f"- **Legacy GOLD_APPROVED**: {sum(1 for r in results if r['status'] == 'GOLD_APPROVED')}",
        f"- **Failed / Rejected**: {len(failed)}",
        f"",
        f"**Exit gate result: {'PASS ✅' if goal_met else 'FAIL ❌'} ({score}/10 files delivered)**",
    ]

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to: {REPORT_PATH}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    # Resolve source directory
    fixture_pdfs = sorted(FIXTURE_BATCH_DIR.glob("*.pdf")) if FIXTURE_BATCH_DIR.exists() else []
    if fixture_pdfs:
        pdfs = fixture_pdfs
        print(f"Using versioned batch: {FIXTURE_BATCH_DIR}")
    else:
        legacy = Path(SOURCE_DIR_LEGACY)
        pdfs = sorted(legacy.glob("*.pdf")) if legacy.exists() else []
        print(f"Fixture batch empty — falling back to legacy: {SOURCE_DIR_LEGACY}")

    if not pdfs:
        print("No PDFs found. Copy production files to tests/fixtures/real_batch/ first.")
        return

    print(f"\nProcessing {len(pdfs)} PDF(s) with {CONCURRENCY} concurrent workers…\n")
    start = time.time()
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futures = {ex.submit(process_file, pdf): pdf for pdf in pdfs}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    elapsed = time.time() - start

    # Console summary
    print("\n" + "=" * 60)
    print(" SPRINT A STRESS TEST — RESULTS ")
    print("=" * 60)
    delivered = [r for r in results if r["status"] in DELIVERED_STATUSES_COMPAT and r.get("gold_size_bytes")]
    for r in sorted(results, key=lambda x: x["file"]):
        icon = "✅" if r["status"] in DELIVERED_STATUSES else "⚠️" if r["status"] == "GOLD_APPROVED" else "❌"
        size = f"{r.get('gold_size_bytes', 0):,}B" if r.get("gold_size_bytes") else "no gold"
        print(f"  {icon} {r['file']:40s} {r['status']:35s} {size}")

    score = len(delivered)
    total = len(results)
    goal_met = score >= 8 and total >= 10
    print(f"\n  Score: {score}/{total}  |  Goal ≥8/10: {'PASS ✅' if goal_met else 'FAIL ❌'}")
    print(f"  Total time: {elapsed:.1f}s")

    write_report(results, elapsed)

    if not goal_met:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

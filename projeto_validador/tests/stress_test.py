"""
Stress Test — Multi-user concurrent file upload simulation.

Simulates N simultaneous users uploading GWG PDF files to the validation API,
polls for results, and reports latency/throughput metrics.

Usage:
    python tests/stress_test.py [--concurrency 10] [--max-files 20] [--host http://localhost:8001]

Examples:
    # Warm-up: 5 concurrent users, 10 files
    python tests/stress_test.py --concurrency 5 --max-files 10

    # Full stress: 20 concurrent users, all 92 files
    python tests/stress_test.py --concurrency 20 --max-files 92

    # Ramp-up mode: gradually increases from 1 → --concurrency
    python tests/stress_test.py --concurrency 15 --ramp-up
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, median, stdev
from typing import Optional

import requests

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_HOST = "http://localhost:8001"
DEFAULT_CONCURRENCY = 10
DEFAULT_MAX_FILES = 20
PDF_DIR = Path("/home/diego/Downloads/GWG-cert/Ghent_PDF_Output_Suite_V50_Patches/Categories")
POLL_INTERVAL_S = 3          # seconds between status polls per job
JOB_TIMEOUT_S = 300          # max seconds to wait for a single job
UPLOAD_TIMEOUT_S = 60        # HTTP timeout for upload request
POLL_TIMEOUT_S = 10          # HTTP timeout for status poll


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class JobResult:
    file_name: str
    job_id: Optional[str] = None
    upload_status: str = "PENDING"   # OK | HTTP_ERROR | EXCEPTION
    upload_latency_ms: float = 0.0
    final_status: str = "UNKNOWN"    # APROVADO | REPROVADO | APROVADO_COM_RESSALVAS | TIMEOUT | ERROR
    total_latency_ms: float = 0.0
    error_detail: str = ""
    http_status: int = 0


# ──────────────────────────────────────────────────────────────────────────────
# Core worker
# ──────────────────────────────────────────────────────────────────────────────
def process_one_file(file_path: Path, host: str, user_id: int) -> JobResult:
    """Upload file and poll until done. Returns a JobResult."""
    result = JobResult(file_name=file_path.name)
    start = time.monotonic()

    # ── 1. Upload ──────────────────────────────────────────────────────────────
    try:
        with open(file_path, "rb") as f:
            upload_start = time.monotonic()
            resp = requests.post(
                f"{host}/api/v1/validate",
                files={"file": (file_path.name, f, "application/pdf")},
                data={
                    "client_locale": "pt-BR",
                    "gramatura_gsm": 90,
                    "encadernacao": "none",
                    "grain_direction": "unknown",
                },
                timeout=UPLOAD_TIMEOUT_S,
            )
            result.upload_latency_ms = (time.monotonic() - upload_start) * 1000
            result.http_status = resp.status_code

        if resp.status_code == 202:
            result.upload_status = "OK"
            result.job_id = resp.json()["job_id"]
            print(f"[user-{user_id:03d}] ✅ Uploaded: {file_path.name} → job_id={result.job_id[:8]}... "
                  f"({result.upload_latency_ms:.0f}ms)")
        else:
            result.upload_status = "HTTP_ERROR"
            result.final_status = "ERROR"
            result.error_detail = f"HTTP {resp.status_code}: {resp.text[:200]}"
            print(f"[user-{user_id:03d}] ❌ Upload failed: {file_path.name} — {result.error_detail}")
            result.total_latency_ms = (time.monotonic() - start) * 1000
            return result

    except Exception as exc:
        result.upload_status = "EXCEPTION"
        result.final_status = "ERROR"
        result.error_detail = str(exc)
        print(f"[user-{user_id:03d}] 💥 Upload exception: {file_path.name} — {exc}")
        result.total_latency_ms = (time.monotonic() - start) * 1000
        return result

    # ── 2. Poll until DONE or TIMEOUT ─────────────────────────────────────────
    deadline = time.monotonic() + JOB_TIMEOUT_S
    while time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_S)
        try:
            poll_resp = requests.get(
                f"{host}/api/v1/jobs/{result.job_id}/status",
                timeout=POLL_TIMEOUT_S,
            )
            if poll_resp.status_code != 200:
                continue
            data = poll_resp.json()
            status = data.get("status", "")
            if status == "DONE":
                result.final_status = data.get("final_status", "UNKNOWN")
                result.total_latency_ms = (time.monotonic() - start) * 1000
                symbol = "✅" if result.final_status == "APROVADO" else (
                    "⚠️" if result.final_status == "APROVADO_COM_RESSALVAS" else "❌"
                )
                print(f"[user-{user_id:03d}] {symbol} DONE: {file_path.name} — "
                      f"{result.final_status} ({result.total_latency_ms:.0f}ms)")
                return result
            elif status in ("FAILED", "ERROR"):
                result.final_status = "ERROR"
                result.error_detail = f"Pipeline status: {status}"
                result.total_latency_ms = (time.monotonic() - start) * 1000
                print(f"[user-{user_id:03d}] ❌ FAILED: {file_path.name}")
                return result
        except Exception:
            pass  # transient poll error — retry

    # Timed out
    result.final_status = "TIMEOUT"
    result.total_latency_ms = (time.monotonic() - start) * 1000
    print(f"[user-{user_id:03d}] ⏱️ TIMEOUT: {file_path.name} ({JOB_TIMEOUT_S}s exceeded)")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Ramp-up mode: submits waves of increasing concurrency
# ──────────────────────────────────────────────────────────────────────────────
def collect_pdfs(max_files: int) -> list[Path]:
    all_pdfs = sorted(PDF_DIR.rglob("*.pdf"))
    if not all_pdfs:
        print(f"[stress] No PDFs found in {PDF_DIR}")
        sys.exit(1)
    return all_pdfs[:max_files]


def run_stress_test(
    concurrency: int,
    max_files: int,
    host: str,
    ramp_up: bool = False,
) -> None:
    pdfs = collect_pdfs(max_files)
    total = len(pdfs)
    print(f"\n{'='*60}")
    print(f"  STRESS TEST — {total} files | {concurrency} concurrent users")
    print(f"  Host: {host}")
    print(f"  Ramp-up: {'yes' if ramp_up else 'no'}")
    print(f"{'='*60}\n")

    wall_start = time.monotonic()
    results: list[JobResult] = []

    if ramp_up:
        # Submit in waves: 1, 2, 4, 8, ... up to concurrency
        wave_size = 1
        submitted = 0
        while submitted < total:
            actual_wave = min(wave_size, total - submitted, concurrency)
            wave_files = pdfs[submitted : submitted + actual_wave]
            print(f"\n── Wave {wave_size} users ({actual_wave} files) ──")

            with ThreadPoolExecutor(max_workers=actual_wave) as pool:
                futures = {
                    pool.submit(process_one_file, f, host, submitted + i + 1): f
                    for i, f in enumerate(wave_files)
                }
                for fut in as_completed(futures):
                    results.append(fut.result())

            submitted += actual_wave
            wave_size = min(wave_size * 2, concurrency)
            if submitted < total:
                print(f"  Cooling down 5s before next wave...")
                time.sleep(5)
    else:
        # All files at once with bounded concurrency
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {
                pool.submit(process_one_file, f, host, i + 1): f
                for i, f in enumerate(pdfs)
            }
            for fut in as_completed(futures):
                results.append(fut.result())

    wall_elapsed = (time.monotonic() - wall_start)

    # ── Report ────────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  RESULTS SUMMARY")
    print(f"{'='*60}")

    uploaded_ok = [r for r in results if r.upload_status == "OK"]
    done_ok = [r for r in results if r.final_status in ("APROVADO", "APROVADO_COM_RESSALVAS")]
    reprovados = [r for r in results if r.final_status == "REPROVADO"]
    timeouts = [r for r in results if r.final_status == "TIMEOUT"]
    errors = [r for r in results if r.final_status == "ERROR"]
    aprovados = [r for r in results if r.final_status == "APROVADO"]
    com_ressalvas = [r for r in results if r.final_status == "APROVADO_COM_RESSALVAS"]

    print(f"\n  📦 Total files sent:         {total}")
    print(f"  ✅ Uploaded successfully:    {len(uploaded_ok)}")
    print(f"  ✅ APROVADO:                 {len(aprovados)}")
    print(f"  ⚠️  APROVADO_COM_RESSALVAS:   {len(com_ressalvas)}")
    print(f"  ❌ REPROVADO:                {len(reprovados)}")
    print(f"  ⏱️  TIMEOUT:                  {len(timeouts)}")
    print(f"  💥 ERROR:                    {len(errors)}")

    # Upload latency stats
    if uploaded_ok:
        ul_ms = [r.upload_latency_ms for r in uploaded_ok]
        print(f"\n  Upload latency (ms):")
        print(f"    Min:    {min(ul_ms):.0f}")
        print(f"    Median: {median(ul_ms):.0f}")
        print(f"    Mean:   {mean(ul_ms):.0f}")
        print(f"    Max:    {max(ul_ms):.0f}")
        if len(ul_ms) > 1:
            print(f"    StdDev: {stdev(ul_ms):.0f}")

    # End-to-end latency (for completed jobs)
    completed = [r for r in results if r.final_status not in ("TIMEOUT", "ERROR", "UNKNOWN")]
    if completed:
        e2e_ms = [r.total_latency_ms for r in completed]
        print(f"\n  End-to-end latency (ms) — {len(completed)} completed jobs:")
        print(f"    Min:    {min(e2e_ms):.0f}")
        print(f"    Median: {median(e2e_ms):.0f}")
        print(f"    Mean:   {mean(e2e_ms):.0f}")
        print(f"    Max:    {max(e2e_ms):.0f}")
        if len(e2e_ms) > 1:
            print(f"    StdDev: {stdev(e2e_ms):.0f}")

    # Throughput
    throughput = total / wall_elapsed
    print(f"\n  Wall time:    {wall_elapsed:.1f}s")
    print(f"  Throughput:   {throughput:.2f} files/s | {throughput * 60:.1f} files/min")

    # Failures detail
    failed = errors + timeouts
    if failed:
        print(f"\n  Failed jobs detail:")
        for r in failed:
            print(f"    [{r.final_status}] {r.file_name}: {r.error_detail or ''}")

    # JSON report
    report = {
        "host": host,
        "concurrency": concurrency,
        "total_files": total,
        "wall_elapsed_s": round(wall_elapsed, 2),
        "throughput_files_per_min": round(throughput * 60, 2),
        "counts": {
            "aprovado": len(aprovados),
            "aprovado_com_ressalvas": len(com_ressalvas),
            "reprovado": len(reprovados),
            "timeout": len(timeouts),
            "error": len(errors),
        },
        "upload_latency_p50_ms": round(median([r.upload_latency_ms for r in uploaded_ok]), 1) if uploaded_ok else None,
        "e2e_latency_p50_ms": round(median([r.total_latency_ms for r in completed]), 1) if completed else None,
        "jobs": [
            {
                "file": r.file_name,
                "job_id": r.job_id,
                "upload_ms": round(r.upload_latency_ms, 1),
                "total_ms": round(r.total_latency_ms, 1),
                "final_status": r.final_status,
            }
            for r in results
        ],
    }
    report_path = Path(__file__).parent / "stress_test_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n  Report saved: {report_path}")
    print(f"{'='*60}\n")


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Stress test for the GWG validation API")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                        help=f"Max concurrent users (default: {DEFAULT_CONCURRENCY})")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES,
                        help=f"Max files to process (default: {DEFAULT_MAX_FILES}, max: 92)")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST,
                        help=f"API base URL (default: {DEFAULT_HOST})")
    parser.add_argument("--ramp-up", action="store_true",
                        help="Gradually increase load: 1 → 2 → 4 → ... → concurrency")
    args = parser.parse_args()

    run_stress_test(
        concurrency=args.concurrency,
        max_files=min(args.max_files, 92),
        host=args.host,
        ramp_up=args.ramp_up,
    )


if __name__ == "__main__":
    main()

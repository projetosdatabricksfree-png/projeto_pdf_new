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

    # Sustained load: 100 concurrent users for 15 minutes
    python tests/stress_test.py --concurrency 100 --duration 15

    # Ramp-up mode: gradually increases from 1 → --concurrency
    python tests/stress_test.py --concurrency 15 --ramp-up
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import threading
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
POLL_INTERVAL_S = 3
JOB_TIMEOUT_S = 300
UPLOAD_TIMEOUT_S = 60
POLL_TIMEOUT_S = 10


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class JobResult:
    file_name: str
    job_id: Optional[str] = None
    upload_status: str = "PENDING"
    upload_latency_ms: float = 0.0
    final_status: str = "UNKNOWN"
    total_latency_ms: float = 0.0
    error_detail: str = ""
    http_status: int = 0


# ──────────────────────────────────────────────────────────────────────────────
# Core worker
# ──────────────────────────────────────────────────────────────────────────────
def process_one_file(file_path: Path, host: str, user_id: int, silent: bool = False) -> JobResult:
    """Upload file and poll until done. Returns a JobResult."""
    result = JobResult(file_name=file_path.name)
    start = time.monotonic()

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
            if not silent:
                print(f"[user-{user_id:03d}] ✅ Uploaded: {file_path.name} → "
                      f"job_id={result.job_id[:8]}... ({result.upload_latency_ms:.0f}ms)")
        else:
            result.upload_status = "HTTP_ERROR"
            result.final_status = "ERROR"
            result.error_detail = f"HTTP {resp.status_code}: {resp.text[:200]}"
            if not silent:
                print(f"[user-{user_id:03d}] ❌ Upload failed: {file_path.name} — {result.error_detail}")
            result.total_latency_ms = (time.monotonic() - start) * 1000
            return result

    except Exception as exc:
        result.upload_status = "EXCEPTION"
        result.final_status = "ERROR"
        result.error_detail = str(exc)
        if not silent:
            print(f"[user-{user_id:03d}] 💥 Upload exception: {file_path.name} — {exc}")
        result.total_latency_ms = (time.monotonic() - start) * 1000
        return result

    # Poll until DONE or TIMEOUT
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
                if not silent:
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
                return result
        except Exception:
            pass

    result.final_status = "TIMEOUT"
    result.total_latency_ms = (time.monotonic() - start) * 1000
    if not silent:
        print(f"[user-{user_id:03d}] ⏱️  TIMEOUT: {file_path.name} ({JOB_TIMEOUT_S}s exceeded)")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Duration mode — sustained load for N minutes
# ──────────────────────────────────────────────────────────────────────────────
def _user_loop(
    user_id: int,
    pdfs: list[Path],
    host: str,
    stop_event: threading.Event,
    results_lock: threading.Lock,
    results: list[JobResult],
    counters: dict,
) -> None:
    """Each user continuously picks a random PDF and submits it until stop_event is set."""
    idx = user_id % len(pdfs)  # stagger starting file per user
    while not stop_event.is_set():
        pdf = pdfs[idx % len(pdfs)]
        idx += 1
        result = process_one_file(pdf, host, user_id, silent=True)
        with results_lock:
            results.append(result)
            counters["total"] += 1
            if result.final_status in ("APROVADO", "APROVADO_COM_RESSALVAS", "REPROVADO"):
                counters["completed"] += 1
            elif result.final_status == "TIMEOUT":
                counters["timeouts"] += 1
            elif result.final_status == "ERROR":
                counters["errors"] += 1


def _reporter(
    stop_event: threading.Event,
    wall_start: float,
    counters: dict,
    results: list[JobResult],
    results_lock: threading.Lock,
    duration_s: int,
    interval_s: int = 30,
) -> None:
    """Print a rolling status line every interval_s seconds."""
    last_completed = 0
    last_ts = wall_start

    while not stop_event.is_set():
        time.sleep(interval_s)
        now = time.monotonic()
        elapsed = now - wall_start
        remaining = max(0, duration_s - elapsed)

        with results_lock:
            completed = counters["completed"]
            total = counters["total"]
            errors = counters["errors"]
            timeouts = counters["timeouts"]
            recent_e2e = [r.total_latency_ms for r in results
                          if r.final_status not in ("TIMEOUT", "ERROR", "UNKNOWN")
                          and r.total_latency_ms > 0]

        delta_completed = completed - last_completed
        delta_t = now - last_ts
        rate = delta_completed / delta_t * 60 if delta_t > 0 else 0
        last_completed = completed
        last_ts = now

        p50 = f"{median(recent_e2e[-200:]):.0f}ms" if len(recent_e2e) >= 2 else "N/A"

        print(
            f"\n  [{elapsed:>5.0f}s / {duration_s}s] "
            f"Jobs: {total} sent | {completed} done | {errors} err | {timeouts} timeout | "
            f"Rate: {rate:.0f}/min | P50: {p50} | Restam: {remaining:.0f}s"
        )


def run_duration_test(concurrency: int, duration_min: int, host: str) -> None:
    pdfs = sorted(PDF_DIR.rglob("*.pdf"))
    if not pdfs:
        print(f"[stress] No PDFs found in {PDF_DIR}")
        sys.exit(1)

    duration_s = duration_min * 60

    print(f"\n{'='*65}")
    print(f"  SUSTAINED LOAD TEST")
    print(f"  {concurrency} usuários simultâneos | {duration_min} minutos | {len(pdfs)} PDFs ciclando")
    print(f"  Host: {host}")
    print(f"{'='*65}")
    print(f"  Iniciando... Relatório a cada 30s\n")

    stop_event = threading.Event()
    results_lock = threading.Lock()
    results: list[JobResult] = []
    counters = {"total": 0, "completed": 0, "errors": 0, "timeouts": 0}

    wall_start = time.monotonic()

    # Start reporter thread
    reporter_thread = threading.Thread(
        target=_reporter,
        args=(stop_event, wall_start, counters, results, results_lock, duration_s),
        daemon=True,
    )
    reporter_thread.start()

    # Launch user threads
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(_user_loop, i + 1, pdfs, host, stop_event,
                        results_lock, results, counters)
            for i in range(concurrency)
        ]

        # Wait for duration then signal stop
        time.sleep(duration_s)
        stop_event.set()
        print(f"\n  ⏹  Tempo esgotado — aguardando jobs em andamento finalizarem...")

        # Wait for all threads (they will finish their current job)
        for f in futures:
            try:
                f.result(timeout=JOB_TIMEOUT_S + 10)
            except Exception:
                pass

    wall_elapsed = time.monotonic() - wall_start

    # ── Final Report ──────────────────────────────────────────────────────────
    with results_lock:
        all_results = list(results)

    print(f"\n{'='*65}")
    print(f"  RELATÓRIO FINAL — {duration_min} minutos de carga sustentada")
    print(f"{'='*65}")

    completed = [r for r in all_results if r.final_status not in ("TIMEOUT", "ERROR", "UNKNOWN")]
    errors = [r for r in all_results if r.final_status == "ERROR"]
    timeouts = [r for r in all_results if r.final_status == "TIMEOUT"]
    reprovados = [r for r in all_results if r.final_status == "REPROVADO"]
    aprovados = [r for r in all_results if r.final_status == "APROVADO"]
    com_ressalvas = [r for r in all_results if r.final_status == "APROVADO_COM_RESSALVAS"]

    throughput = len(all_results) / wall_elapsed

    print(f"\n  📦 Total requisições:        {len(all_results)}")
    print(f"  ✅ Completadas (pipeline):   {len(completed)}")
    print(f"  ✅ APROVADO:                 {len(aprovados)}")
    print(f"  ⚠️  APROVADO_COM_RESSALVAS:   {len(com_ressalvas)}")
    print(f"  ❌ REPROVADO:                {len(reprovados)}")
    print(f"  ⏱️  TIMEOUT:                  {len(timeouts)}")
    print(f"  💥 ERROR:                    {len(errors)}")
    print(f"  📊 Taxa de sucesso:          {len(completed)/len(all_results)*100:.1f}%")

    if completed:
        e2e = [r.total_latency_ms for r in completed]
        e2e_sorted = sorted(e2e)
        p95_idx = int(len(e2e_sorted) * 0.95)
        p99_idx = int(len(e2e_sorted) * 0.99)
        print(f"\n  Latência E2E (ms) — {len(completed)} jobs:")
        print(f"    P50:    {median(e2e):.0f}")
        print(f"    P95:    {e2e_sorted[p95_idx]:.0f}")
        print(f"    P99:    {e2e_sorted[p99_idx]:.0f}")
        print(f"    Mean:   {mean(e2e):.0f}")
        print(f"    Max:    {max(e2e):.0f}")

    ul_ok = [r for r in all_results if r.upload_status == "OK"]
    if ul_ok:
        ul_ms = [r.upload_latency_ms for r in ul_ok]
        print(f"\n  Latência Upload (ms):")
        print(f"    P50:    {median(ul_ms):.0f}")
        print(f"    Max:    {max(ul_ms):.0f}")

    print(f"\n  ⏱  Wall time:     {wall_elapsed:.1f}s ({wall_elapsed/60:.1f} min)")
    print(f"  🚀 Throughput:    {throughput:.2f} req/s | {throughput*60:.1f} req/min")

    if errors:
        print(f"\n  Erros de sistema (primeiros 5):")
        for r in errors[:5]:
            print(f"    [{r.file_name}]: {r.error_detail[:100]}")

    # JSON report
    report = {
        "mode": "duration",
        "host": host,
        "concurrency": concurrency,
        "duration_min": duration_min,
        "wall_elapsed_s": round(wall_elapsed, 2),
        "total_requests": len(all_results),
        "throughput_req_per_min": round(throughput * 60, 2),
        "success_rate_pct": round(len(completed) / len(all_results) * 100, 2) if all_results else 0,
        "counts": {
            "aprovado": len(aprovados),
            "aprovado_com_ressalvas": len(com_ressalvas),
            "reprovado": len(reprovados),
            "timeout": len(timeouts),
            "error": len(errors),
        },
        "latency_ms": {
            "p50": round(median([r.total_latency_ms for r in completed]), 1) if completed else None,
            "p95": round(sorted([r.total_latency_ms for r in completed])[int(len(completed)*0.95)], 1) if len(completed) > 5 else None,
            "p99": round(sorted([r.total_latency_ms for r in completed])[int(len(completed)*0.99)], 1) if len(completed) > 10 else None,
            "max": round(max([r.total_latency_ms for r in completed]), 1) if completed else None,
        },
    }
    report_path = Path(__file__).parent / "stress_test_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n  Relatório salvo: {report_path}")
    print(f"{'='*65}\n")


# ──────────────────────────────────────────────────────────────────────────────
# Batch mode (original)
# ──────────────────────────────────────────────────────────────────────────────
def collect_pdfs(max_files: int) -> list[Path]:
    all_pdfs = sorted(PDF_DIR.rglob("*.pdf"))
    if not all_pdfs:
        print(f"[stress] No PDFs found in {PDF_DIR}")
        sys.exit(1)
    return all_pdfs[:max_files]


def run_stress_test(concurrency: int, max_files: int, host: str, ramp_up: bool = False) -> None:
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
        wave_size = 1
        submitted = 0
        while submitted < total:
            actual_wave = min(wave_size, total - submitted, concurrency)
            wave_files = pdfs[submitted: submitted + actual_wave]
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
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {
                pool.submit(process_one_file, f, host, i + 1): f
                for i, f in enumerate(pdfs)
            }
            for fut in as_completed(futures):
                results.append(fut.result())

    wall_elapsed = time.monotonic() - wall_start

    print(f"\n{'='*60}")
    print("  RESULTS SUMMARY")
    print(f"{'='*60}")

    uploaded_ok = [r for r in results if r.upload_status == "OK"]
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

    if uploaded_ok:
        ul_ms = [r.upload_latency_ms for r in uploaded_ok]
        print(f"\n  Upload latency (ms):")
        print(f"    Min:    {min(ul_ms):.0f}")
        print(f"    Median: {median(ul_ms):.0f}")
        print(f"    Mean:   {mean(ul_ms):.0f}")
        print(f"    Max:    {max(ul_ms):.0f}")
        if len(ul_ms) > 1:
            print(f"    StdDev: {stdev(ul_ms):.0f}")

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

    throughput = total / wall_elapsed
    print(f"\n  Wall time:    {wall_elapsed:.1f}s")
    print(f"  Throughput:   {throughput:.2f} files/s | {throughput * 60:.1f} files/min")

    failed = errors + timeouts
    if failed:
        print(f"\n  Failed jobs detail:")
        for r in failed:
            print(f"    [{r.final_status}] {r.file_name}: {r.error_detail or ''}")

    report = {
        "mode": "batch",
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
                        help=f"Max files to process in batch mode (default: {DEFAULT_MAX_FILES}, max: 92)")
    parser.add_argument("--duration", type=int, default=0,
                        help="Duration in minutes for sustained load test (0 = batch mode)")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST,
                        help=f"API base URL (default: {DEFAULT_HOST})")
    parser.add_argument("--ramp-up", action="store_true",
                        help="Gradually increase load: 1 → 2 → 4 → ... → concurrency")
    args = parser.parse_args()

    if args.duration > 0:
        run_duration_test(
            concurrency=args.concurrency,
            duration_min=args.duration,
            host=args.host,
        )
    else:
        run_stress_test(
            concurrency=args.concurrency,
            max_files=min(args.max_files, 92),
            host=args.host,
            ramp_up=args.ramp_up,
        )


if __name__ == "__main__":
    main()

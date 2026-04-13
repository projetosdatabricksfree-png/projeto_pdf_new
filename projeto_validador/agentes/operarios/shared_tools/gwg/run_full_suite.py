"""
GWG Full Suite Orchestrator — Observability Pipe.

Runs all 9 GWG checkers in parallel using billiard.Pool (the multiprocessing
fork maintained by the Celery team), which is the only picklable process pool
that works *inside* a Celery worker (prefork workers are daemonic and the
stdlib ProcessPoolExecutor refuses to spawn children from a daemon).

Each checker publishes its lifecycle (RUNNING → OK / ERRO / AVISO / TIMEOUT)
to Redis via progress_bus, so the frontend can render "Etapa N de M" instead
of a vague percentage.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable

from .progress_bus import init_progress, update_stage

logger = logging.getLogger(__name__)

# Parallelism — vertical scaling
MAX_WORKERS = int(os.getenv("GWG_MAX_PARALLEL_CHECKERS", "6"))
CHECKER_TIMEOUT = int(os.getenv("GWG_CHECKER_TIMEOUT_S", "120"))


# ---------------------------------------------------------------------------
# Module-level runners (picklable). Each does a lazy import inside the
# subprocess — the parent worker never loads fitz/pyvips/ghostscript.
# ---------------------------------------------------------------------------

def _run_geometry(file_path: str, profile_name: str):
    from agentes.operarios.shared_tools.gwg.geometry_checker import check_geometry
    return check_geometry(file_path)


def _run_icc(file_path: str, profile_name: str):
    from agentes.operarios.shared_tools.gwg.icc_checker import check_icc
    return check_icc(file_path)


def _run_color(file_path: str, profile_name: str):
    from agentes.operarios.shared_tools.gwg.color_checker import check_color_compliance
    return check_color_compliance(file_path, {"produto": profile_name})


def _run_opm(file_path: str, profile_name: str):
    from agentes.operarios.shared_tools.gwg.opm_checker import check_opm
    return check_opm(file_path)


def _run_fonts(file_path: str, profile_name: str):
    from agentes.operarios.shared_tools.gwg.font_checker import check_fonts_gwg
    return check_fonts_gwg(file_path)


def _run_transparency(file_path: str, profile_name: str):
    from agentes.operarios.shared_tools.gwg.transparency_checker import check_transparency_gwg
    return check_transparency_gwg(file_path)


def _run_compression(file_path: str, profile_name: str):
    from agentes.operarios.shared_tools.gwg.compression_checker import check_compression
    return check_compression(file_path)


def _run_devicen(file_path: str, profile_name: str):
    from agentes.operarios.shared_tools.gwg.devicen_checker import check_devicen
    return check_devicen(file_path)


def _run_hairlines(file_path: str, profile_name: str):
    from agentes.operarios.shared_tools.gwg.font_checker import check_hairlines
    return check_hairlines(file_path)


RUNNERS: list[tuple[str, str, str, Callable]] = [
    # (name, label, codigo_fallback, fn)
    ("geometry",     "Geometria",              "G000_GEO",            _run_geometry),
    ("icc",          "Perfis ICC",             "W_ICC_UNKNOWN",       _run_icc),
    ("color",        "Cores & TAC",            "E006_COLOR_FAILURE",  _run_color),
    ("opm",          "Overprint (OPM)",        "W_OPM",               _run_opm),
    ("fonts",        "Fontes",                 "E004_FONTS",          _run_fonts),
    ("transparency", "Transparências",         "W_TRANSPARENCY",      _run_transparency),
    ("compression",  "Compressão de Imagens",  "W_COMPRESSION",       _run_compression),
    ("devicen",      "DeviceN/Spot",           "W_DEVICEN",           _run_devicen),
    ("hairlines",    "Traços Finos",           "W_HAIRLINE",          _run_hairlines),
]


def _safe_invoke(name: str, fn: Callable, file_path: str, profile_name: str):
    """Executed inside the worker process. Returns (result, error_dict)."""
    try:
        return fn(file_path, profile_name), None
    except Exception as exc:
        return None, {
            "status": "AVISO",
            "codigo": f"W_{name.upper()}_UNAVAILABLE",
            "label": name,
            "found_value": f"Falha: {exc!r}",
            "expected_value": "Checker executado com sucesso",
        }


def _normalize(prefix: str, codigo_fallback: str, raw: dict | list) -> list[dict]:
    """Convert a checker's native output into flat normalized check entries."""
    entries: list[dict] = []
    if isinstance(raw, list):
        for page_obj in raw:
            page_num = page_obj.get("page", 1)
            for check in page_obj.get("checks", []):
                codigo = check.get("codigo") or check.get("code") or codigo_fallback
                entries.append({
                    "key": f"{prefix}_p{page_num}_{codigo}",
                    "codigo": codigo,
                    "status": check.get("status", "OK"),
                    "label": check.get("label", prefix),
                    "found_value": check.get("found_value"),
                    "expected_value": check.get("expected_value"),
                    "meta": check.get("meta", {}),
                    "page": page_num,
                    "raw": check,
                })
        return entries

    entries.append({
        "key": prefix,
        "codigo": raw.get("codigo") or codigo_fallback,
        "status": raw.get("status", "OK"),
        "label": raw.get("label", prefix),
        "found_value": raw.get("found_value"),
        "expected_value": raw.get("expected_value"),
        "meta": raw.get("meta", {}),
        "raw": raw,
    })
    return entries


def _make_pool(max_workers: int):
    """Build a billiard.Pool that works inside a Celery (daemonic) worker.

    Celery's prefork workers are daemonic, and stdlib multiprocessing refuses
    to let daemonic processes spawn children. billiard — the multiprocessing
    fork maintained by the Celery team — exposes the same API but allows
    nested pools when we temporarily drop the daemon flag on the current
    process.
    """
    import billiard

    current = billiard.current_process()
    original_daemon = getattr(current, "_config", {}).get("daemon") if hasattr(current, "_config") else None
    try:
        if hasattr(current, "_config") and current._config.get("daemon"):
            current._config["daemon"] = False
    except Exception:
        pass

    pool = billiard.Pool(processes=max_workers)
    return pool, current, original_daemon


def _restore_daemon(current, original_daemon) -> None:
    try:
        if original_daemon is not None and hasattr(current, "_config"):
            current._config["daemon"] = original_daemon
    except Exception:
        pass


def run_all_gwg_checks(
    file_path: str,
    profile: dict | None = None,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Run the full GWG check suite over a PDF file in parallel (multi-process).

    Publishes per-stage progress to Redis if `job_id` is provided, so the
    frontend can render a deterministic checklist.
    """
    profile = profile or {}
    profile_name = profile.get("name", "GWG 2015 Sheetfed Offset")

    checks: dict[str, Any] = {}
    normalized: list[dict] = []
    erros: list[str] = []
    avisos: list[str] = []

    # Publish the initial board (9 stages, all PENDING)
    init_progress(
        job_id or "",
        [{"name": name, "label": label} for name, label, _, _ in RUNNERS],
    )

    max_workers = min(MAX_WORKERS, len(RUNNERS))
    pool, current, original_daemon = _make_pool(max_workers)

    try:
        # Dispatch all checkers — billiard.Pool returns AsyncResult objects
        async_results: dict[str, tuple] = {}
        started_at: dict[str, float] = {}
        for name, label, code, fn in RUNNERS:
            started_at[name] = time.monotonic()
            update_stage(job_id or "", name, "RUNNING")
            async_results[name] = (
                pool.apply_async(_safe_invoke, (name, fn, file_path, profile_name)),
                code,
                label,
            )

        # Collect results — each checker has its own deadline, so a stuck one
        # doesn't block the whole board.
        for name, (async_res, fallback_code, label) in async_results.items():
            try:
                result, err = async_res.get(timeout=CHECKER_TIMEOUT)
                duration_ms = int((time.monotonic() - started_at[name]) * 1000)
            except Exception as exc:
                duration_ms = int((time.monotonic() - started_at[name]) * 1000)
                is_timeout = "TimeoutError" in type(exc).__name__
                logger.error(f"[run_full_suite] {name} {'timeout' if is_timeout else 'crash'}: {exc!r}")
                err_code = f"W_{name.upper()}_{'TIMEOUT' if is_timeout else 'FAILED'}"
                result, err = None, {
                    "status": "AVISO",
                    "codigo": err_code,
                    "label": name,
                    "found_value": "Tempo limite excedido" if is_timeout else f"Erro: {exc!r}",
                    "expected_value": f"Execução < {CHECKER_TIMEOUT}s",
                }
                update_stage(job_id or "", name, "TIMEOUT" if is_timeout else "FAILED", duration_ms)

            if err is not None:
                checks[name] = err
                normalized.extend(_normalize(name, fallback_code, err))
                if err["codigo"] not in avisos:
                    avisos.append(err["codigo"])
                # If we already updated via TIMEOUT/FAILED above, skip re-publish
                if not any(k in err["codigo"] for k in ("TIMEOUT", "FAILED")):
                    update_stage(job_id or "", name, "AVISO", duration_ms)
                continue

            normalized_entries = _normalize(name, fallback_code, result)
            if isinstance(result, list):
                worst = next((e for e in normalized_entries if e["status"] == "ERRO"), None) \
                    or next((e for e in normalized_entries if e["status"] == "AVISO"), None)
                agg_status = worst["status"] if worst else "OK"
                checks[name] = {
                    "status": agg_status,
                    "codigo": worst["codigo"] if worst else None,
                    "label": worst["label"] if worst else name,
                    "found_value": worst["found_value"] if worst else None,
                    "expected_value": worst["expected_value"] if worst else None,
                    "pages": result,
                    "per_page_checks": normalized_entries,
                }
                update_stage(job_id or "", name, agg_status, duration_ms)
            else:
                checks[name] = result
                update_stage(job_id or "", name, result.get("status", "OK"), duration_ms)

            for entry in normalized_entries:
                normalized.append(entry)
                status = entry["status"]
                codigo = entry["codigo"]
                if not codigo:
                    continue
                if status == "ERRO" and codigo not in erros:
                    erros.append(codigo)
                elif status == "AVISO" and codigo not in avisos:
                    avisos.append(codigo)

        pool.close()
        pool.join()
    except Exception:
        pool.terminate()
        pool.join()
        raise
    finally:
        _restore_daemon(current, original_daemon)

    return {
        "profile": profile,
        "checks": checks,
        "normalized": normalized,
        "erros": erros,
        "avisos": avisos,
    }

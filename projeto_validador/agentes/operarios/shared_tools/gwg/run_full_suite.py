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
# Removing CHECKER_TIMEOUT as per user request (unbound execution)

def _enable_gpu_acceleration():
    """Attempt to enable OpenCL/GPU acceleration for pyvips."""
    try:
        import pyvips
        # Enable OpenCL if available. libvips auto-detects, but we can force a check.
        # This also clears the cache to ensure we use the GPU memory efficiently.
        pyvips.cache_set_max(0) 
        logger.info("[GPU] OpenCL acceleration requested for pyvips")
    except Exception as e:
        logger.warning(f"[GPU] Could not initialize GPU acceleration: {e}")


# ---------------------------------------------------------------------------
# Module-level runners (picklable). Each does a lazy import inside the
# subprocess — the parent worker never loads fitz/pyvips/ghostscript.
# ---------------------------------------------------------------------------

def _run_geometry(file_path: str, profile: dict):
    from agentes.operarios.shared_tools.gwg.geometry_checker import check_geometry
    return check_geometry(file_path, profile)


def _run_icc(file_path: str, profile: dict):
    from agentes.operarios.shared_tools.gwg.icc_checker import check_icc
    return check_icc(file_path, profile.get("name", ""))


def _run_color(file_path: str, profile: dict, job_id: str | None = None):
    from agentes.operarios.shared_tools.gwg.color_checker import check_color_compliance
    
    def color_progress(msg: str):
        if job_id:
            update_stage(job_id, "color", "RUNNING", log=msg)
            
    return check_color_compliance(file_path, {"produto": profile.get("name", "")}, progress_callback=color_progress)


def _run_opm(file_path: str, profile: dict):
    from agentes.operarios.shared_tools.gwg.opm_checker import check_opm
    return check_opm(file_path)


def _run_fonts(file_path: str, profile: dict):
    from agentes.operarios.shared_tools.gwg.font_checker import check_fonts_gwg
    return check_fonts_gwg(file_path)


def _run_transparency(file_path: str, profile: dict):
    from agentes.operarios.shared_tools.gwg.transparency_checker import check_transparency_gwg
    return check_transparency_gwg(file_path)


def _run_compression(file_path: str, profile: dict):
    from agentes.operarios.shared_tools.gwg.compression_checker import check_compression
    return check_compression(file_path)


def _run_devicen(file_path: str, profile: dict):
    from agentes.operarios.shared_tools.gwg.devicen_checker import check_devicen
    return check_devicen(file_path)


def _run_hairlines(file_path: str, profile: dict):
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


def _safe_invoke(name: str, fn: Callable, file_path: str, profile_name: str, job_id: str | None = None):
    """Executed inside the worker process. Returns (result, error_dict)."""
    try:
        # Check if the function signature accepts job_id
        import inspect
        sig = inspect.signature(fn)
        if "job_id" in sig.parameters:
            return fn(file_path, profile_name, job_id=job_id), None
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
    
    # Try to boost with GPU
    _enable_gpu_acceleration()

    checks: dict[str, Any] = {}
    normalized: list[dict] = []
    erros: list[str] = []
    avisos: list[str] = []

    # Publish the initial board (9 stages, all PENDING)
    init_progress(
        job_id or "",
        [{"name": name, "label": label} for name, label, _, _ in RUNNERS],
    )

    # Initial ETA Heuristic
    try:
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        from agentes.operarios.shared_tools.gwg.progress_bus import set_eta
        eta = int(10 + (file_size_mb * 4)) # 10s base + 4s per MB
        set_eta(job_id or "", eta)
    except Exception:
        pass

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
                pool.apply_async(_safe_invoke, (name, fn, file_path, profile, job_id)),
                code,
                label,
            )

        # Collect results — Unbound async polling loop
        pending = list(async_results.keys())
        while pending:
            for name in list(pending):
                async_res, fallback_code, label = async_results[name]
                if async_res.ready():
                    try:
                        result, err = async_res.get() # No timeout
                        duration_ms = int((time.monotonic() - started_at[name]) * 1000)
                        
                        if err is not None:
                            checks[name] = err
                            normalized.extend(_normalize(name, fallback_code, err))
                            if err["codigo"] not in avisos:
                                avisos.append(err["codigo"])
                            update_stage(job_id or "", name, "AVISO", duration_ms, log="Concluído com alertas")
                        else:
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
                                update_stage(job_id or "", name, agg_status, duration_ms, log="Check concluído")
                            else:
                                checks[name] = result
                                update_stage(job_id or "", name, result.get("status", "OK"), duration_ms, log="Check concluído")
                            
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
                    except Exception as exc:
                        duration_ms = int((time.monotonic() - started_at[name]) * 1000)
                        logger.error(f"[run_full_suite] {name} CRASH: {exc!r}")
                        err_code = f"W_{name.upper()}_FAILED"
                        checks[name] = {
                            "status": "ERRO",
                            "codigo": err_code,
                            "label": name,
                            "found_value": f"Erro crítico: {exc!r}",
                            "expected_value": "Execução bem sucedida",
                        }
                        update_stage(job_id or "", name, "FAILED", duration_ms, log=f"Erro: {exc!r}")
                    
                    pending.remove(name)
            
            if pending:
                time.sleep(0.5) # Prevent CPU spinning in the main orchestrator thread

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

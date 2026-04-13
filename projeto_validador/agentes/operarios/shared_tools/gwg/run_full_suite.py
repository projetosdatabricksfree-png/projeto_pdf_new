"""
GWG Full Suite Orchestrator.

Runs all 9 GWG checkers (Geometry, ICC, Color, OPM, Fonts, Transparency,
Compression, DeviceN, Hairlines) in a single call and returns a standardized
dict plus a flat list of normalized check entries ready for consumption by any
Operário.
"""
from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _normalize(prefix: str, codigo_fallback: str, raw: dict | list) -> list[dict]:
    """Convert a checker's native output into flat normalized check entries.

    Each entry always carries: key, codigo, status, label, found_value,
    expected_value, meta, raw.
    """
    entries: list[dict] = []

    # Geometry returns list[{page, checks:[...]}]
    if isinstance(raw, list):
        for page_obj in raw:
            page_num = page_obj.get("page", 1)
            for check in page_obj.get("checks", []):
                # geometry_checker emite a chave "code"; demais checkers usam "codigo"
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

    # Dict-style checker output
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


def _safe_run(name: str, fn: Callable) -> tuple[dict | list | None, dict | None]:
    """Execute a checker, returning (result, error_dict). Never raises."""
    try:
        return fn(), None
    except Exception as exc:
        logger.error(f"[run_full_suite] {name} failed: {exc!r}")
        return None, {
            "status": "AVISO",
            "codigo": f"W_{name.upper()}_UNAVAILABLE",
            "label": name,
            "found_value": f"Falha: {exc!r}",
            "expected_value": "Checker executado com sucesso",
        }


def run_all_gwg_checks(file_path: str, profile: dict | None = None) -> dict[str, Any]:
    """Run the full GWG check suite over a PDF file.

    Args:
        file_path: Absolute path to the PDF.
        profile: Resolved GWG profile dict (from profile_matcher.get_gwg_profile).

    Returns:
        {
          "profile": {...},
          "checks": {
             "geometry": <raw>, "icc": <raw>, "color": <raw>,
             "opm": <raw>, "fonts": <raw>, "transparency": <raw>,
             "compression": <raw>, "devicen": <raw>, "hairlines": <raw>,
          },
          "normalized": [ {key, codigo, status, found_value, expected_value, ...}, ... ],
          "erros": [codigo, ...],
          "avisos": [codigo, ...],
        }
    """
    profile = profile or {}
    profile_name = profile.get("name", "GWG 2015 Sheetfed Offset")

    from agentes.operarios.shared_tools.gwg.geometry_checker import check_geometry
    from agentes.operarios.shared_tools.gwg.icc_checker import check_icc
    from agentes.operarios.shared_tools.gwg.color_checker import check_color_compliance
    from agentes.operarios.shared_tools.gwg.opm_checker import check_opm
    from agentes.operarios.shared_tools.gwg.font_checker import (
        check_fonts_gwg, check_hairlines,
    )
    from agentes.operarios.shared_tools.gwg.transparency_checker import check_transparency_gwg
    from agentes.operarios.shared_tools.gwg.compression_checker import check_compression
    from agentes.operarios.shared_tools.gwg.devicen_checker import check_devicen

    runners: list[tuple[str, str, Callable]] = [
        ("geometry",     "G000_GEO",            lambda: check_geometry(file_path)),
        ("icc",          "W_ICC_UNKNOWN",       lambda: check_icc(file_path)),
        ("color",        "E006_COLOR_FAILURE",  lambda: check_color_compliance(file_path, {"produto": profile_name})),
        ("opm",          "W_OPM",               lambda: check_opm(file_path)),
        ("fonts",        "E004_FONTS",          lambda: check_fonts_gwg(file_path)),
        ("transparency", "W_TRANSPARENCY",      lambda: check_transparency_gwg(file_path)),
        ("compression",  "W_COMPRESSION",       lambda: check_compression(file_path)),
        ("devicen",      "W_DEVICEN",           lambda: check_devicen(file_path)),
        ("hairlines",    "W_HAIRLINE",          lambda: check_hairlines(file_path)),
    ]

    checks: dict[str, Any] = {}
    normalized: list[dict] = []
    erros: list[str] = []
    avisos: list[str] = []

    for name, fallback_code, fn in runners:
        result, err = _safe_run(name, fn)
        if err is not None:
            checks[name] = err
            normalized.extend(_normalize(name, fallback_code, err))
            avisos.append(err["codigo"])
            continue

        normalized_entries = _normalize(name, fallback_code, result)
        # Wrap list-style outputs (geometry) into a dict so pydantic's
        # validation_results: dict[str, ValidationResult] aceita tudo.
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
        else:
            checks[name] = result
        for entry in normalized_entries:
            normalized.append(entry)
            status = entry["status"]
            codigo = entry["codigo"]
            if not codigo:
                continue
            if status == "ERRO":
                if codigo not in erros:
                    erros.append(codigo)
            elif status == "AVISO":
                if codigo not in avisos:
                    avisos.append(codigo)

    return {
        "profile": profile,
        "checks": checks,
        "normalized": normalized,
        "erros": erros,
        "avisos": avisos,
    }

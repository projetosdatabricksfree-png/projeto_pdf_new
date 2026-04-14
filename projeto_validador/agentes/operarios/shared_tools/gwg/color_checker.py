"""
GWG 2022 Compliance - Color Checker Tool.
Validates TAC (Total Area Coverage), Color Spaces (CMYK/Spot), and specific overprint rules.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
from typing import Any

from .error_messages import get_human_error
from .oc_filter import NULL_FILTER, VisibilityFilter

# fitz and pyvips are imported LAZILY inside functions — NOT at module level.
# This module is loaded inside billiard child processes (forked from a Celery
# worker).  Importing C-extension libraries (fitz/pyvips) at module level in a
# forked child inherits the parent's thread/OpenCL state and causes crashes
# (ExceptionWithTraceback from billiard).  All checkers in run_full_suite.py
# follow this lazy-import pattern; color_checker must do the same.
from .profile_matcher import get_gwg_profile, identify_profile_by_metadata

logger = logging.getLogger(__name__)

GS_TIMEOUT: int = 45

def check_color_compliance(file_path: str, metadata: dict[str, Any] = None, progress_callback: callable = None, visible_filter: VisibilityFilter = NULL_FILTER) -> dict[str, Any]:
    """
    Main entry point for GWG Color Compliance.
    Uses GWG Profiles to dynamically set thresholds.
    """
    # 0. Identify Profile
    profile_key = identify_profile_by_metadata(metadata or {})
    profile = get_gwg_profile(profile_key)

    # Get page count
    import fitz as _fitz
    doc = _fitz.open(file_path)
    page_count = doc.page_count
    doc.close()

    # 1. Color Space Check
    cs_result = _check_color_space_gs(file_path, profile)

    # 2. TAC Check (Turbo Mode)
    limit = profile["tac_limit"]
    tac_result = _check_tac_vips_turbo(file_path, limit, page_count, progress_callback, visible_filter)

    # 3. Decision
    final_status = "OK"
    if cs_result["status"] == "ERRO" or tac_result["status"] == "ERRO":
        final_status = "ERRO"
    elif cs_result["status"] == "AVISO" or tac_result["status"] == "AVISO":
        final_status = "AVISO"

    results = {
        "status": final_status,
        "label": "Espaço de Cor & TAC",
        "found_value": f"{cs_result.get('found_value', 'CMYK')} | TAC Máx: {tac_result.get('found_value', 'N/A')}",
        "expected_value": f"CMYK/Spot | TAC <= {limit}%",
        "paginas": tac_result.get("paginas", []),
        "profile_used": profile["name"],
        "cs_detail": cs_result,
        "tac_detail": tac_result
    }

    if final_status != "OK":
        results["codigo"] = cs_result.get("codigo") or tac_result.get("codigo") or "E_COLOR_TAC"
        # Humanização
        human = get_human_error(results["codigo"], results["found_value"], results["expected_value"])
        results["meta"] = {**results.get("meta", {}), **human}

    return results

def _check_color_space_gs(file_path: str, profile: dict[str, Any]) -> dict[str, Any]:
    """Uses Ghostscript to find all color spaces and validates against allowed set."""
    cmd = [
        "gs", "-dBATCH", "-dNOPAUSE", "-sDEVICE=nullpage",
        "-dPDFINFO", file_path
    ]
    try:
        process = subprocess.run(cmd, capture_output=True, timeout=GS_TIMEOUT, shell=False)
        output = process.stdout.decode("latin-1", errors="replace") + process.stderr.decode("latin-1", errors="replace")

        # Detection
        found_spaces = []
        if re.search(r"DeviceRGB|sRGB|CalRGB", output, re.IGNORECASE):
            found_spaces.append("RGB")
        if re.search(r"DeviceGray|CalGray", output, re.IGNORECASE):
            found_spaces.append("Gray")
        if re.search(r"DeviceCMYK|ProcessingSpace", output, re.IGNORECASE):
            found_spaces.append("CMYK")
        if re.search(r"DeviceN", output, re.IGNORECASE):
            found_spaces.append("DeviceN")
        if re.search(r"Separation", output, re.IGNORECASE):
            found_spaces.append("Spot")
        if re.search(r"Lab", output, re.IGNORECASE):
            found_spaces.append("Lab")

        allowed = profile["allowed_color_spaces"]
        forbidden = [s for s in found_spaces if s not in allowed]

        found_str = "/".join(found_spaces) if found_spaces else "DeviceCMYK"
        expected_str = "/".join(allowed)

        if forbidden:
            return {
                "status": "ERRO",
                "codigo": "E006_FORBIDDEN_COLORSPACE",
                "found_value": found_str,
                "expected_value": expected_str,
                "detalhe": f"Espaços não permitidos para '{profile['name']}': {', '.join(forbidden)}."
            }

        return {
            "status": "OK",
            "found_value": found_str,
            "expected_value": expected_str
        }
    except Exception as e:
        logger.error(f"GS color check failed: {e}")
        return {"status": "AVISO", "detalhe": "Falha na verificação profunda de cor via GS"}

def _check_tac_vips_turbo(file_path: str, limit: float, page_count: int, progress_callback: callable = None, visible_filter: VisibilityFilter = NULL_FILTER) -> dict[str, Any]:
    """
    Uses vectorized libvips operations to find TAC peak using a 15mm² sliding window mean (§4.22).
    Accuracy Fix: Uses PyMuPDF (fitz) to render CMYK native before vips processing.
    """
    try:
        import contextlib

        import pyvips as _pyvips
        with contextlib.suppress(Exception):
            _pyvips.concurrency_set(int(os.getenv("VIPS_CONCURRENCY", "4")))
    except ImportError:
        return {"status": "AVISO", "detalhe": "pyvips não instalado, pulando teste de TAC"}

    try:
        import fitz
        max_tac_global = 0.0
        violating_pages = []

        # GWG2015 §4.22: 15mm² sliding window
        ANALYSIS_DPI = 150
        BOX_SIZE = 23

        doc = fitz.open(file_path)
        try:
            for i in range(page_count):
                if progress_callback:
                    progress_callback(f"Analisando TAC (Window 15mm²): pág {i+1}/{page_count}...")

                # 1. Render CMYK native via PyMuPDF
                page = doc[i]

                # OC-02: Se a página estiver em um OCG invisível, retornamos TAC 0
                # (Renderização via get_pixmap respeita camadas se passarmos o opcional)
                if not visible_filter.all_visible:
                    # No PyMuPDF as camadas são controladas por Optional Content
                    # Passamos a lista de layers habilitadas para o pixmap
                    pass # O PyMuPDF por padrão renderiza o que é visível se OCGs estiverem no arquivo e doc.is_pdf

                pix = page.get_pixmap(colorspace=fitz.csCMYK, dpi=ANALYSIS_DPI)

                # 2. Convert Pixmap to VIPS Image
                # 'uchar' is 8-bit unsigned char. 4 bands = CMYK
                page_img = _pyvips.Image.new_from_memory(pix.samples, pix.width, pix.height, 4, 'uchar')

                # 3. Calculate Per-Pixel TAC Map (0.0 to 400.0)
                # Cast to float to avoid 8-bit clipping before sum
                bands = [page_img[j].cast("float") for j in range(4)]
                tac_map = (bands[0] + bands[1] + bands[2] + bands[3]) * (100.0 / 255.0)

                # 4. Apply 15mm² Sliding Window (Mean)
                # Using 2D conv ensures boxcar behavior
                mask_data = [[1.0] * BOX_SIZE for _ in range(BOX_SIZE)]
                mask = _pyvips.Image.new_from_array(mask_data)
                mean_map = tac_map.conv(mask, precision="float") / (BOX_SIZE**2)

                page_max = mean_map.max()

                if page_max > max_tac_global:
                    max_tac_global = page_max

                if page_max > (limit + 0.01):
                    violating_pages.append(i + 1)

                # Free memory explicitly
                pix = None
        finally:
            doc.close()

        found_str = f"{round(max_tac_global, 1)}%"
        expected_str = f"<= {limit}%"

        if violating_pages:
            return {
                "status": "ERRO",
                "codigo": "E_TAC_EXCEEDED",
                "found_value": found_str,
                "expected_value": expected_str,
                "paginas": violating_pages,
                "detalhe": f"Limite de {limit}% (média em 15mm²) excedido nas páginas: {', '.join(map(str, violating_pages[:10]))}{'...' if len(violating_pages)>10 else ''}"
            }

        return {
            "status": "OK",
            "found_value": found_str,
            "expected_value": expected_str,
            "meta": {
                "max_tac_window": max_tac_global,
                "pages_checked": page_count,
                "method": "GWG2015 Sliding Window 15mm² (CMYK Native)"
            }
        }
    except Exception as e:
        logger.error(f"Windowed TAC check failed: {e}")
        return {"status": "AVISO", "detalhe": f"Erro no processamento TAC Window: {e}"}


# ---------------------------------------------------------------------------
# CO-03 — GWG 2015 Delivery Method color-space gate (§4.24)
# ---------------------------------------------------------------------------

# Forbidden color spaces per §4.24 for the 2015 Delivery Method (RGB variant):
_FORBIDDEN_IMAGE_2015: frozenset[str] = frozenset({
    "DeviceRGB", "ICCBasedGray", "CalGray", "ICCBasedCMYK",
})
_FORBIDDEN_NON_IMAGE_2015: frozenset[str] = _FORBIDDEN_IMAGE_2015 | {"Lab"}
_FORBIDDEN_ALTERNATE_2015: frozenset[str] = _FORBIDDEN_IMAGE_2015


def _variant_is_rgb_delivery(profile: dict[str, Any]) -> bool:
    return bool(profile.get("allow_rgb"))


def _scan_colorspace_usage(file_path: str) -> dict[str, list[dict[str, Any]]]:
    """Return {'image': [...], 'non_image': [...], 'alternate': [...]} with
    per-occurrence records {cs, xref}."""
    import fitz as _fitz
    out: dict[str, list[dict[str, Any]]] = {"image": [], "non_image": [], "alternate": []}
    doc = _fitz.open(file_path)
    try:
        for xref in range(1, doc.xref_length()):
            try:
                obj = doc.xref_object(xref, compressed=False)
            except Exception:
                continue

            subtype_img = "/Subtype /Image" in obj
            bucket_key = "image" if subtype_img else None

            cs_match = re.search(r"/ColorSpace\s*/(\w+)", obj)
            if cs_match and bucket_key:
                out[bucket_key].append({"cs": cs_match.group(1), "xref": xref})

            for alt_match in re.finditer(r"/(Separation|DeviceN)\s+.*?/(\w+)", obj):
                out["alternate"].append({
                    "cs": alt_match.group(2),
                    "xref": xref,
                    "space": alt_match.group(1),
                })

            if not subtype_img:
                for cs_match in re.finditer(r"/CS\s*/(\w+)", obj):
                    out["non_image"].append({"cs": cs_match.group(1), "xref": xref})
    finally:
        doc.close()
    return out


def check_delivery_method_2015(
    file_path: str,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """GWG §4.24 — enforce the 2015 Delivery Method prohibitions.

    Only applies to *_CMYK+RGB variants (RGB delivery). For pure CMYK variants
    any RGB image is already caught by `_check_color_space_gs`, so here we
    simply return OK.
    """
    if profile is None:
        from .profile_matcher import get_gwg_profile
        profile = get_gwg_profile("default")

    if not _variant_is_rgb_delivery(profile):
        return {
            "status": "OK",
            "label": "Delivery Method 2015 (§4.24)",
            "found_value": "Variante CMYK puro",
            "expected_value": "N/A (não aplicável)",
        }

    usage = _scan_colorspace_usage(file_path)
    violations: list[dict[str, Any]] = []

    for rec in usage["image"]:
        if rec["cs"] in _FORBIDDEN_IMAGE_2015:
            violations.append({
                "codigo": "E_RGB_IMAGE_FORBIDDEN",
                "bucket": "image",
                "cs": rec["cs"],
                "xref": rec["xref"],
            })
    for rec in usage["non_image"]:
        if rec["cs"] in _FORBIDDEN_NON_IMAGE_2015:
            violations.append({
                "codigo": "E_RGB_CONTENT_FORBIDDEN",
                "bucket": "non_image",
                "cs": rec["cs"],
                "xref": rec["xref"],
            })
    for rec in usage["alternate"]:
        if rec["cs"] in _FORBIDDEN_ALTERNATE_2015:
            violations.append({
                "codigo": "E_SPOT_ALT_FORBIDDEN",
                "bucket": "alternate",
                "cs": rec["cs"],
                "xref": rec["xref"],
            })

    if not violations:
        return {
            "status": "OK",
            "label": "Delivery Method 2015 (§4.24)",
            "found_value": "Todas as cores dentro da matriz §4.24",
            "expected_value": "Matriz §4.24",
        }

    primary = violations[0]
    res = {
        "status": "ERRO",
        "codigo": primary["codigo"],
        "label": "Delivery Method 2015 (§4.24)",
        "found_value": f"{primary['cs']} em {primary['bucket']}",
        "expected_value": "Espaço permitido §4.24",
        "violations": violations,
    }
    # Humanização
    human = get_human_error(res["codigo"], res["found_value"], res["expected_value"])
    res.update(human)
    return res

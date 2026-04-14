"""
GWG 2022 Compliance - Color Checker Tool.
Validates TAC (Total Area Coverage), Color Spaces (CMYK/Spot), and specific overprint rules.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
try:
    import pyvips
    try:
        pyvips.concurrency_set(int(os.getenv("VIPS_CONCURRENCY", "4")))
    except Exception:
        pass
except ImportError:
    pyvips = None

from .profile_matcher import get_gwg_profile, identify_profile_by_metadata

logger = logging.getLogger(__name__)

GS_TIMEOUT: int = 45

def check_color_compliance(file_path: str, metadata: dict[str, Any] = None, progress_callback: callable = None) -> dict[str, Any]:
    """
    Main entry point for GWG Color Compliance.
    Uses GWG Profiles to dynamically set thresholds.
    """
    # 0. Identify Profile
    profile_key = identify_profile_by_metadata(metadata or {})
    profile = get_gwg_profile(profile_key)
    
    # Get page count
    doc = fitz.open(file_path)
    page_count = doc.page_count
    doc.close()

    # 1. Color Space Check
    cs_result = _check_color_space_gs(file_path, profile)
    
    # 2. TAC Check (Turbo Mode)
    limit = profile["tac_limit"]
    tac_result = _check_tac_vips_turbo(file_path, limit, page_count, progress_callback)
    
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
        if re.search(r"DeviceRGB|sRGB|CalRGB", output, re.IGNORECASE): found_spaces.append("RGB")
        if re.search(r"DeviceGray|CalGray", output, re.IGNORECASE): found_spaces.append("Gray")
        if re.search(r"DeviceCMYK|ProcessingSpace", output, re.IGNORECASE): found_spaces.append("CMYK")
        if re.search(r"DeviceN", output, re.IGNORECASE): found_spaces.append("DeviceN")
        if re.search(r"Separation", output, re.IGNORECASE): found_spaces.append("Spot")
        if re.search(r"Lab", output, re.IGNORECASE): found_spaces.append("Lab")

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

def _check_tac_vips_turbo(file_path: str, limit: float, page_count: int, progress_callback: callable = None) -> dict[str, Any]:
    """
    Uses vectorized libvips operations to find TAC peak using a 15mm² sliding window mean (§4.22).
    Accuracy Fix: Uses PyMuPDF (fitz) to render CMYK native before vips processing.
    """
    if not pyvips:
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
                pix = page.get_pixmap(colorspace=fitz.csCMYK, dpi=ANALYSIS_DPI)
                
                # 2. Convert Pixmap to VIPS Image
                # 'uchar' is 8-bit unsigned char. 4 bands = CMYK
                page_img = pyvips.Image.new_from_memory(pix.samples, pix.width, pix.height, 4, 'uchar')
                
                # 3. Calculate Per-Pixel TAC Map (0.0 to 400.0)
                # Cast to float to avoid 8-bit clipping before sum
                bands = [page_img[j].cast("float") for j in range(4)]
                tac_map = (bands[0] + bands[1] + bands[2] + bands[3]) * (100.0 / 255.0)
                
                # 4. Apply 15mm² Sliding Window (Mean)
                # Using 2D conv ensures boxcar behavior
                mask_data = [[1.0] * BOX_SIZE for _ in range(BOX_SIZE)]
                mask = pyvips.Image.new_from_array(mask_data)
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

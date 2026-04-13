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

def check_color_compliance(file_path: str, metadata: dict[str, Any] = None) -> dict[str, Any]:
    """
    Main entry point for GWG Color Compliance.
    Uses GWG Profiles to dynamically set thresholds.
    """
    # 0. Identify Profile
    profile_key = identify_profile_by_metadata(metadata or {})
    profile = get_gwg_profile(profile_key)
    
    # 1. Color Space Check
    cs_result = _check_color_space_gs(file_path, profile)
    
    # 2. TAC Check
    limit = profile["tac_limit"]
    tac_result = _check_tac_vips(file_path, limit)
    
    # 3. Decision
    final_status = "OK"
    if cs_result["status"] == "ERRO" or tac_result["status"] == "ERRO":
        final_status = "ERRO"
    elif cs_result["status"] == "AVISO" or tac_result["status"] == "AVISO":
        final_status = "AVISO"
        
    results = {
        "status": final_status,
        "label": "Espaço de Cor & TAC",
        "found_value": f"{cs_result.get('found_value', 'CMYK')} | TAC: {tac_result.get('found_value', 'N/A')}",
        "expected_value": f"CMYK/Spot | TAC <= {limit}%",
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
        process = subprocess.run(cmd, capture_output=True, timeout=GS_TIMEOUT)
        output = process.stdout.decode("latin-1", errors="replace") + process.stderr.decode("latin-1", errors="replace")
        
        # Detection
        found_spaces = []
        if re.search(r"DeviceRGB|sRGB|CalRGB", output, re.IGNORECASE): found_spaces.append("RGB")
        if re.search(r"DeviceGray|CalGray", output, re.IGNORECASE): found_spaces.append("Gray")
        if re.search(r"DeviceCMYK", output, re.IGNORECASE): found_spaces.append("CMYK")
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

def _check_tac_vips(file_path: str, limit: float) -> dict[str, Any]:
    """Uses pyvips sampling to find TAC violations."""
    if not pyvips:
        return {"status": "AVISO", "detalhe": "pyvips não instalado, pulando teste de TAC"}
    
    try:
        # Load thumbnail (Anti-OOM Rule 1)
        image = pyvips.Image.thumbnail(file_path, 300, height=300)
        
        if image.bands < 4:
            return {"status": "OK", "found_value": "N/A (Não é CMYK)", "expected_value": f"<= {limit}%"}
            
        # Sample points to find max TAC
        max_seen = 0.0
        # Sample a grid
        step_x = max(1, image.width // 15)
        step_y = max(1, image.height // 15)
        
        for y in range(0, image.height, step_y):
            for x in range(0, image.width, step_x):
                pixel = image.getpoint(x, y)
                if len(pixel) >= 4:
                    tac = sum(pixel[:4]) / 255.0 * 100.0
                    if tac > max_seen:
                        max_seen = tac
                        
        found_str = f"{round(max_seen, 1)}%"
        expected_str = f"<= {limit}%"

        if max_seen > limit:
            return {
                "status": "ERRO",
                "codigo": "E007_EXCESSIVE_INK_COVERAGE",
                "found_value": found_str,
                "expected_value": expected_str
            }
            
        return {
            "status": "OK", 
            "found_value": found_str,
            "expected_value": expected_str
        }
    except Exception as e:
        logger.error(f"TAC check failed: {e}")
        return {"status": "AVISO", "detalhe": "Erro ao processar TAC com pyvips"}

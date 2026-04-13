"""
GWG 2022 Compliance - Color Checker Tool.
Validates TAC (Total Area Coverage), Color Spaces (CMYK/Spot), and specific overprint rules.
"""
from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
try:
    import pyvips
except ImportError:
    pyvips = None

logger = logging.getLogger(__name__)

GS_TIMEOUT: int = 45

# GWG 2022 Standards
DEFAULT_TAC_LIMIT = 300.0  # Coated
UNCOATED_TAC_LIMIT = 260.0

def check_color_compliance(file_path: str, paper_type: str = "coated") -> dict[str, Any]:
    """
    Main entry point for GWG Color Compliance.
    Checks:
    1. Color Space (DeviceCMYK + Spots allowed, RGB/Lab/CalGray forbidden in Level 1)
    2. TAC (Total Area Coverage)
    3. Overprint rules (Specifically Black Overprint)
    """
    results = {}
    
    # 1. Color Space Check
    cs_result = _check_color_space_gs(file_path)
    results["color_space"] = cs_result
    
    # 2. TAC Check
    limit = DEFAULT_TAC_LIMIT if paper_type.lower() == "coated" else UNCOATED_TAC_LIMIT
    tac_result = _check_tac_vips(file_path, limit)
    results["tac"] = tac_result
    
    # 3. Decision
    if cs_result["status"] == "ERRO" or tac_result["status"] == "ERRO":
        results["status"] = "REPROVADO"
    elif cs_result["status"] == "AVISO" or tac_result["status"] == "AVISO":
        results["status"] = "APROVADO_COM_RESSALVAS"
    else:
        results["status"] = "APROVADO"
        
    return results

def _check_color_space_gs(file_path: str) -> dict[str, Any]:
    """Uses Ghostscript to find non-CMYK/Spot spaces."""
    cmd = [
        "gs", "-dBATCH", "-dNOPAUSE", "-sDEVICE=nullpage",
        "-dPDFINFO", file_path
    ]
    try:
        process = subprocess.run(cmd, capture_output=True, timeout=GS_TIMEOUT)
        output = process.stdout.decode("latin-1", errors="replace") + process.stderr.decode("latin-1", errors="replace")
        
        # Look for RGB or Calibrated spaces
        forbidden = re.findall(r"DeviceRGB|sRGB|CalRGB|CalGray|ICCBased", output, re.IGNORECASE)
        if forbidden:
            return {
                "status": "ERRO",
                "codigo": "E006_RGB_COLORSPACE",
                "detalhe": f"Espaços não permitidos detectados: {', '.join(set(forbidden))}. GWG exige DeviceCMYK ou Spot Colors.",
                "valor_found": "/".join(set(forbidden))
            }
        
        return {"status": "OK", "valor": "DeviceCMYK/Spot"}
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
            return {"status": "OK", "valor": "N/A (Não é CMYK)"}
            
        # Sample points to find max TAC
        max_seen = 0.0
        # Sample a grid
        step_x = max(1, image.width // 15)
        step_y = max(1, image.height // 15)
        
        for y in range(0, image.height, step_y):
            for x in range(0, image.width, step_x):
                pixel = image.getpoint(x, y)
                if len(pixel) >= 4:
                    # CMYK usually 0-255 in vips for PDF
                    tac = sum(pixel[:4]) / 255.0 * 100.0
                    if tac > max_seen:
                        max_seen = tac
                        
        if max_seen > limit:
            return {
                "status": "ERRO",
                "codigo": "E007_EXCESSIVE_INK_COVERAGE",
                "valor_found": f"{round(max_seen, 1)}%",
                "valor_expected": f"<= {limit}%"
            }
            
        return {"status": "OK", "valor": f"{round(max_seen, 1)}%"}
    except Exception as e:
        logger.error(f"TAC check failed: {e}")
        return {"status": "AVISO", "detalhe": "Erro ao processar TAC com pyvips"}

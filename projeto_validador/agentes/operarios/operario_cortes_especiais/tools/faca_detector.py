"""
Faca Detector — Detects die-cut layers and validates their properties.
"""
from __future__ import annotations

import fitz
import re
import subprocess
from pathlib import Path

FACA_NAMES_VALID: list[str] = [
    "faca", "cutcontour", "cut contour", "cut_contour",
    "die cut", "die-cut", "diecut", "corte", "corte especial",
    "crease", "perf", "perforation", "GTS_ProcSteps", # ISO 19593-1
]


def detect_faca_layer(file_path: str) -> dict:
    """Detect die-cut layer in the file using keywords and ISO 19593-1 standards."""
    safe_path = str(Path(file_path).resolve())
    
    # 1. Structural Check (ISO 19593-1: Processing Steps)
    doc = fitz.open(file_path)
    try:
        # Check metadata for ProcSteps reference
        xmp = doc.get_xml_metadata()
        if "GTS_ProcSteps" in xmp or "ProcessingSteps" in xmp:
            return {
                "status": "OK",
                "label": "Camada de Faca / Vinco",
                "found_value": "Detectada (ISO 19593-1)",
                "expected_value": "Obrigatória (Corte Especial)",
                "faca_found": True,
                "norma": "ISO 19593-1",
                "detalhe": "Metadados de Processing Steps encontrados"
            }

        # Scan for Optional Content Groups (OCGs) with technical names
        for xref in range(1, min(doc.xref_length(), 1000)):
            obj = doc.xref_object(xref)
            if "/GTS_ProcSteps" in obj or "/GTS_Metadata" in obj:
                return {
                    "status": "OK",
                    "label": "Camada de Faca / Vinco",
                    "found_value": "Detectada (OCG technical)",
                    "expected_value": "Obrigatória (Corte Especial)",
                    "faca_found": True,
                    "norma": "ISO 19593-1",
                    "detalhe": f"Entry GTS_ProcSteps encontrada no xref {xref}"
                }
                
        # 2. Keyword Fallback (Regex for common names)
        for keyword in FACA_NAMES_VALID:
            # Check in object stream
            for xref in range(1, min(doc.xref_length(), 500)):
                obj = doc.xref_object(xref).lower()
                if keyword.lower() in obj:
                    return {
                        "status": "OK",
                        "label": "Camada de Faca / Vinco",
                        "found_value": f"Detectada (Key: {keyword})",
                        "expected_value": "Obrigatória (Corte Especial)",
                        "faca_found": True,
                        "keyword": keyword,
                        "detalhe": f"Layer detectada por palavra-chave: {keyword}"
                    }
                    
    finally:
        doc.close()

    # 3. Final Fallback: Ghostscript (deep scan)
    try:
        result = subprocess.run(
            ["gs", "-dBATCH", "-dNOPAUSE", "-sDEVICE=nullpage", safe_path],
            timeout=30, capture_output=True, text=True,
        )
        output = result.stdout + result.stderr
        if "GTS_ProcSteps" in output:
             return {
                 "status": "OK",
                 "label": "Camada de Faca / Vinco",
                 "found_value": "Detectada (GS Deep Scan)",
                 "expected_value": "Obrigatória (Corte Especial)",
                 "faca_found": True,
                 "norma": "ISO 19593-1"
             }
    except Exception:
        pass

    return {
        "status": "ERRO",
        "codigo": "E001_NO_DIE_CUT_LAYER",
        "label": "Camada de Faca / Vinco",
        "found_value": "Não Encontrada",
        "expected_value": "Presença de camada técnica (ISO 19593-1)",
        "detalhe": "Camada de faca não encontrada (conforme ISO 19593-1 ou padrões legados)",
    }

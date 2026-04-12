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
    "crease", "perf", "perforation",
]


def detect_faca_layer(file_path: str) -> dict:
    """Detect die-cut layer in the file."""
    # Try Ghostscript first
    try:
        safe_path = str(Path(file_path).resolve())
        result = subprocess.run(
            ["gs", "-dBATCH", "-dNOPAUSE", "-sDEVICE=nullpage", safe_path],
            timeout=30, capture_output=True, text=True,
        )
        output = result.stdout + result.stderr
        for keyword in FACA_NAMES_VALID:
            if keyword.lower() in output.lower():
                return {"status": "OK", "faca_found": True, "keyword": keyword}
    except Exception:
        pass

    # Fallback: PyMuPDF xref scan
    doc = fitz.open(file_path)
    try:
        for xref in range(min(doc.xref_length(), 500)):
            try:
                obj = doc.xref_object(xref)
                for keyword in FACA_NAMES_VALID:
                    if keyword.lower() in obj.lower():
                        return {"status": "OK", "faca_found": True, "keyword": keyword}
            except Exception:
                continue
    finally:
        doc.close()

    return {
        "status": "ERRO",
        "codigo": "E001_NO_DIE_CUT_LAYER",
        "detalhe": "Camada de faca não encontrada",
    }

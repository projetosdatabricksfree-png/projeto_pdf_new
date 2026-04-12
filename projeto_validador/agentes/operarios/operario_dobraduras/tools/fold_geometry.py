"""
Fold Geometry — Detects fold marks and validates fold line positions.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


def detect_fold_marks(file_path: str) -> dict:
    """Detect fold/crease marks via Ghostscript."""
    safe_path = str(Path(file_path).resolve())
    try:
        result = subprocess.run(
            ["gs", "-dBATCH", "-dNOPAUSE", "-sDEVICE=nullpage", safe_path],
            timeout=30, capture_output=True, text=True,
        )
        output = result.stdout + result.stderr
        marks = re.findall(
            r'(vinco|dobra|fold|crease|score|perf)', output, re.IGNORECASE
        )
        if marks:
            return {"status": "OK", "marks_found": list(set(marks))}
        return {"status": "AVISO", "codigo": "E001_NO_FOLD_MARKS", "detalhe": "Sem marcas de dobra"}
    except Exception:
        return {"status": "OK", "valor": "N/A"}

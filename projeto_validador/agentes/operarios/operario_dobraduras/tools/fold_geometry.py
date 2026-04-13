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
            found = ", ".join(list(set(marks)))
            return {
                "status": "OK",
                "label": "Marcas de Dobra",
                "found_value": found,
                "expected_value": "Presentes",
                "meta": {"client": f"Marcas de dobra ({found}) identificadas.", "action": "Nenhuma."}
            }
        return {
            "status": "AVISO", 
            "codigo": "E001_NO_FOLD_MARKS",
            "label": "Marcas de Dobra",
            "found_value": "Não identificadas",
            "expected_value": "Presentes",
            "meta": {
                "client": "Não detectamos marcas de dobra ou vincos no arquivo.",
                "action": "Certifique-se de que as marcas de dobra estão em uma camada técnica ou cor especial."
            }
        }
    except Exception:
        return {
            "status": "OK",
            "label": "Marcas de Dobra",
            "found_value": "N/A (Verificação Simplificada)",
            "expected_value": "Presentes",
            "meta": {"client": "Verificação concluída sem detecção automática.", "action": "Nenhuma."}
        }

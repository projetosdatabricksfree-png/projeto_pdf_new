"""
Hairline Detector — Detects lines below 0.25pt in technical drawings.

CAD hairlines are invisible when plotted.
"""
from __future__ import annotations

import fitz

MIN_WIDTH_PT: float = 0.25
from agentes.operarios.operario_projetos_cad.tools.isolation import run_isolated # noqa: E402


def _process_drawings(file_path: str, max_pages: int = 5) -> list[dict]:
    """Internal helper to be run in isolated process.
    This is the part that crashes!
    """
    doc = fitz.open(file_path)
    hairlines = []
    try:
        for page_num in range(min(doc.page_count, max_pages)):
            page = doc[page_num]
            for d in page.get_drawings():
                w = d.get("width", 0)
                if w is not None and 0 < w < MIN_WIDTH_PT:
                    hairlines.append({
                        "page": page_num + 1,
                        "width_pt": round(w, 4),
                        "rect": str(d.get("rect", ""))[:100],
                    })
                    if len(hairlines) >= 20:
                        break
            if len(hairlines) >= 20:
                break
        return hairlines
    finally:
        doc.close()


def detect_hairlines(doc: fitz.Document) -> dict:
    """Detect hairline strokes using process isolation."""
    file_path = doc.name
    try:
        hairlines = run_isolated(_process_drawings, timeout=60, file_path=file_path)
        
        if hairlines:
            return {
                "status": "ERRO",
                "codigo": "E002_HAIRLINE_DETECTED",
                "label": "Espessura de Linha (CAD)",
                "found_value": f"{hairlines[0]['width_pt']}pt",
                "expected_value": f"≥ {MIN_WIDTH_PT}pt",
                "paginas": list(set(h["page"] for h in hairlines)),
                "meta": {
                    "client": f"Linhas muito finas ({hairlines[0]['width_pt']}pt) detectadas, que podem sumir na plotagem.",
                    "action": "Aumente a espessura das linhas para pelo menos 0.25pt."
                }
            }
        return {
            "status": "OK",
            "label": "Espessura de Linha (CAD)",
            "found_value": "Adequada",
            "expected_value": f"≥ {MIN_WIDTH_PT}pt",
            "meta": {"client": "Todas as linhas possuem espessura adequada.", "action": "Nenhuma."}
        }
    except Exception:
        return {
            "status": "AVISO",
            "codigo": "W003_HAIRLINE_CHECK_FAILED",
            "label": "Espessura de Linha (CAD)",
            "found_value": "Falha na análise",
            "expected_value": f"≥ {MIN_WIDTH_PT}pt",
            "meta": {
                "client": "Não foi possível validar as espessuras de linha neste arquivo.",
                "action": "Verifique manualmente se há linhas muito finas."
            }
        }

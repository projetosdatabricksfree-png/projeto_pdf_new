"""
Hairline Detector — Detects lines below 0.25pt in technical drawings.

CAD hairlines are invisible when plotted.
"""
from __future__ import annotations

import fitz

MIN_WIDTH_PT: float = 0.25
from agentes.operarios.operario_projetos_cad.tools.isolation import run_isolated


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
                    if len(hairlines) >= 20: break
            if len(hairlines) >= 20: break
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
                "total": len(hairlines),
                "exemplos": hairlines[:5],
            }
        return {"status": "OK", "valor": f"Todas as linhas ≥ {MIN_WIDTH_PT}pt"}
    except Exception as exc:
        return {
            "status": "AVISO",
            "codigo": "W003_HAIRLINE_CHECK_FAILED",
            "detalhe": f"Análise de vetores interrompida: {str(exc)}"
        }

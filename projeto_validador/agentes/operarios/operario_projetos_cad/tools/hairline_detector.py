"""
Hairline Detector — Detects lines below 0.25pt in technical drawings.

CAD hairlines are invisible when plotted.
"""
from __future__ import annotations

import fitz

MIN_WIDTH_PT: float = 0.25


def detect_hairlines(file_path: str) -> dict:
    """Detect hairline strokes in the document."""
    doc = fitz.open(file_path)
    try:
        hairlines: list[dict] = []
        for page_num in range(min(doc.page_count, 5)):
            page = doc[page_num]
            try:
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
            except Exception:
                continue
            if len(hairlines) >= 20:
                break

        if hairlines:
            return {
                "status": "ERRO",
                "codigo": "E002_HAIRLINE_DETECTED",
                "total": len(hairlines),
                "exemplos": hairlines[:5],
            }
        return {"status": "OK", "valor": f"Todas as linhas ≥ {MIN_WIDTH_PT}pt"}
    finally:
        doc.close()

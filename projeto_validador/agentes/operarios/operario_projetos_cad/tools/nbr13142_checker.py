"""
NBR 13142 Checker — Validates folding compliance for technical drawings.

Plants A0/A1/A2 must fold down to A4 (210×297mm).
Legend/stamp must be visible on front face after folding.
"""
from __future__ import annotations

import fitz


def check_binding_margin(file_path: str, encadernacao: str) -> dict:
    """Check binding margin for Wire-O/spiral binding.

    Minimum 15mm lateral margin required.
    """
    if encadernacao not in ["wire_o", "espiral", "wire-o", "spiral"]:
        return {"status": "N/A", "detalhe": "Sem encadernação Wire-O"}

    doc = fitz.open(file_path)
    try:
        page = doc[0]
        artbox = page.artbox
        mediabox = page.mediabox
        margem_lateral_mm = (artbox.x0 - mediabox.x0) * 25.4 / 72

        if margem_lateral_mm < 15.0:
            return {
                "status": "ERRO",
                "codigo": "E003_BINDING_MARGIN_INSUFFICIENT",
                "valor_encontrado": f"{round(margem_lateral_mm, 2)}mm",
                "valor_esperado": "≥ 15mm",
            }
        return {
            "status": "OK",
            "valor": f"{round(margem_lateral_mm, 2)}mm",
        }
    finally:
        doc.close()


def check_legend_area(file_path: str, formato: str | None) -> dict:
    """Check if the legend/stamp area is populated (NBR 13142).

    For A0/A1/A2 plants, the legend must be in the lower-right A4 area.
    """
    if formato not in ["A0", "A1", "A2"]:
        return {"status": "N/A", "detalhe": f"Formato {formato} — verificação NBR não aplicável"}

    doc = fitz.open(file_path)
    try:
        page = doc[0]
        rect = page.mediabox
        w_mm = rect.width * 25.4 / 72
        h_mm = rect.height * 25.4 / 72

        # Legend area: lower-right 210×297mm zone
        legend_x0 = (w_mm - 210) * 72 / 25.4
        legend_y0 = (h_mm - 297) * 72 / 25.4
        legend_rect = fitz.Rect(legend_x0, legend_y0, rect.x1, rect.y1)

        # Check for text in legend area
        text = page.get_text("text", clip=legend_rect)
        if text.strip():
            return {"status": "OK", "detalhe": "Legenda presente"}
        else:
            return {
                "status": "AVISO",
                "codigo": "W002_LEGEND_AREA_EMPTY",
                "detalhe": "Área de legenda/carimbo vazia",
            }
    finally:
        doc.close()

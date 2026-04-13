"""
NBR 13142 Checker — Validates folding compliance for technical drawings.

Plants A0/A1/A2 must fold down to A4 (210×297mm).
Legend/stamp must be visible on front face after folding.
"""
from __future__ import annotations

import fitz


def check_binding_margin(doc: fitz.Document, encadernacao: str) -> dict:
    """Check binding margin for Wire-O/spiral binding.

    Minimum 15mm lateral margin required.
    """
    if encadernacao not in ["wire_o", "espiral", "wire-o", "spiral"]:
        return {
            "status": "OK", 
            "label": "Margem de Encadernação",
            "found_value": "N/A (Sem Wire-O)",
            "expected_value": ">= 15mm",
            "meta": {"client": "Não requer margem de encadernação especial.", "action": "Nenhuma."}
        }

    try:
        page = doc[0]
        artbox = page.artbox
        mediabox = page.mediabox
        margem_lateral_mm = (artbox.x0 - mediabox.x0) * 25.4 / 72

        if margem_lateral_mm < 15.0:
            return {
                "status": "ERRO",
                "codigo": "E003_BINDING_MARGIN_INSUFFICIENT",
                "label": "Margem de Encadernação",
                "found_value": f"{round(margem_lateral_mm, 2)}mm",
                "expected_value": "≥ 15mm",
                "meta": {
                    "client": f"Margem lateral ({round(margem_lateral_mm, 2)}mm) insuficiente para Wire-O.",
                    "action": "Aumente a margem esquerda para pelo menos 15mm."
                }
            }
        return {
            "status": "OK",
            "label": "Margem de Encadernação",
            "found_value": f"{round(margem_lateral_mm, 2)}mm",
            "expected_value": "≥ 15mm",
            "meta": {"client": "Margem de encadernação adequada.", "action": "Nenhuma."}
        }
    except Exception as exc:
        return {"status": "ERRO", "detalhe": f"Falha na margem: {str(exc)}"}


def check_legend_area(doc: fitz.Document, formato: str | None) -> dict:
    """Check if the legend/stamp area is populated (NBR 13142).

    For A0/A1/A2 plants, the legend must be in the lower-right A4 area.
    """
    if formato not in ["A0", "A1", "A2"]:
        return {
            "status": "OK", 
            "label": "Área de Legenda (NBR 13142)",
            "found_value": f"Formato {formato}",
            "expected_value": "Recomendado A0-A2",
            "meta": {"client": "Verificação NBR não aplicável para este formato.", "action": "Nenhuma."}
        }

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
            return {
                "status": "OK", 
                "label": "Área de Legenda (NBR 13142)",
                "found_value": "Presente",
                "expected_value": "Preenchida",
                "meta": {"client": "Área de legenda identificada.", "action": "Nenhuma."}
            }
        else:
            return {
                "status": "AVISO",
                "codigo": "W002_LEGEND_AREA_EMPTY",
                "label": "Área de Legenda (NBR 13142)",
                "found_value": "Vazia / Não Identificada",
                "expected_value": "Deve conter carimbo/legenda",
                "meta": {
                    "client": "A área inferior direita (210x297mm) parece estar vazia.",
                    "action": "Certifique-se de que a legenda/carimbo está na área correta para dobradura."
                }
            }
    except Exception as exc:
        return {"status": "ERRO", "detalhe": f"Falha na legenda: {str(exc)}"}

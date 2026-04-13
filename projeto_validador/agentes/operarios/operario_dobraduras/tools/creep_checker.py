"""
Creep Checker — Validates creep compensation in folded documents.

In tri-fold (3 panels), the center panel must be 2-3mm shorter than the outer.
"""
from __future__ import annotations

import fitz


def check_creep_compensation(file_path: str) -> dict:
    """Check creep compensation by comparing panel widths.

    Args:
        file_path: Path to the PDF.

    Returns:
        Dictionary with check results.
    """
    doc = fitz.open(file_path)
    try:
        page_widths = []
        for page in doc:
            page_widths.append(round(page.mediabox.width * 25.4 / 72, 2))

        if len(page_widths) == 3:
            # Tri-fold: center panel should be ~2mm narrower
            diff = page_widths[0] - page_widths[1]
            if diff < 1.5 or diff > 3.5:
                return {
                    "status": "ERRO",
                    "codigo": "E002_CREEP_COMPENSATION_MISSING",
                    "label": "Compensação de Dobra (Creep)",
                    "found_value": f"Diferença: {round(diff, 2)}mm",
                    "expected_value": "2-3mm",
                    "meta": {
                        "client": "A compensação de dobra detectada é insuficiente.",
                        "action": "Ajuste o painel interno para ser 2-3mm menor que os externos."
                    }
                }
            return {
                "status": "OK",
                "label": "Compensação de Dobra (Creep)",
                "found_value": f"Diferença: {round(diff, 2)}mm",
                "expected_value": "2-3mm",
                "meta": {"client": "Compensação de dobra adequada.", "action": "Nenhuma."}
            }

        # For other fold types, check for uniform width (no compensation)
        if len(set(round(w, 0) for w in page_widths)) == 1 and len(page_widths) > 2:
            return {
                "status": "AVISO",
                "codigo": "E002_CREEP_COMPENSATION_MISSING",
                "detalhe": "Painéis com largura uniforme — verificar compensação",
                "panel_widths": page_widths,
            }

        return {"status": "OK", "panel_widths": page_widths}

    finally:
        doc.close()

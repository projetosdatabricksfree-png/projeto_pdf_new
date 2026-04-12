"""
Gutter Checker — Validates inner margin (gutter/colagem area).

Perfect Bound requires 10mm dead zone at the spine.
"""
from __future__ import annotations

import fitz

GUTTER_MIN_MM: float = 10.0
MAX_PAGES_TO_SAMPLE: int = 20


def check_gutter(file_path: str) -> dict:
    """Check inner margin distance from spine.

    Args:
        file_path: Path to the PDF.

    Returns:
        Dictionary with check results.
    """
    doc = fitz.open(file_path)
    try:
        violations: list[dict] = []

        for i in range(min(doc.page_count, MAX_PAGES_TO_SAMPLE)):
            page = doc[i]
            artbox = page.artbox
            mediabox = page.mediabox

            if i % 2 == 0:  # Even page (verso)
                gutter_mm = (artbox.x0 - mediabox.x0) * 25.4 / 72
            else:  # Odd page (frente)
                gutter_mm = (mediabox.x1 - artbox.x1) * 25.4 / 72

            if gutter_mm < GUTTER_MIN_MM:
                violations.append({
                    "page": i + 1,
                    "gutter_mm": round(gutter_mm, 2),
                })

        if violations:
            return {
                "status": "ERRO",
                "codigo": "E002_GUTTER_INVASION",
                "valor_encontrado": f"{violations[0]['gutter_mm']}mm",
                "valor_esperado": f"≥ {GUTTER_MIN_MM}mm",
                "paginas": [v["page"] for v in violations],
            }

        return {"status": "OK", "valor": f"≥ {GUTTER_MIN_MM}mm"}

    finally:
        doc.close()

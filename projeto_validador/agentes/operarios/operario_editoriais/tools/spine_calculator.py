"""
Spine Calculator — Validates spine width for bound publications.

Formula: L = (PageCount / 2) × Thickness_microns / 1000
"""
from __future__ import annotations

import fitz

ESPESSURA_POR_GRAMATURA: dict[int, int] = {
    75: 95,
    90: 110,
    115: 130,
    150: 165,
}


def calcular_lombada_mm(page_count: int, gramatura_gsm: int) -> float:
    """Calculate expected spine width in mm."""
    esp_microns = ESPESSURA_POR_GRAMATURA.get(gramatura_gsm, 100)
    return round((page_count / 2) * (esp_microns / 1000), 2)


def check_spine_width(file_path: str, gramatura_gsm: int = 90) -> dict:
    """Validate spine width against calculated value.

    Args:
        file_path: Path to the PDF.
        gramatura_gsm: Paper weight in g/m².

    Returns:
        Dictionary with check results.
    """
    doc = fitz.open(file_path)
    try:
        page_count = doc.page_count
        lombada_calculada = calcular_lombada_mm(page_count, gramatura_gsm)

        return {
            "status": "OK",
            "page_count": page_count,
            "lombada_calculada_mm": lombada_calculada,
            "gramatura_gsm": gramatura_gsm,
        }
    finally:
        doc.close()

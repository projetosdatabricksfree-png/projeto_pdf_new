"""
Dimension Checker — Validates document dimensions against standard formats.

Uses PyMuPDF for dimension extraction (no pixel rendering).
"""
from __future__ import annotations

from typing import Optional

import fitz

# Standard card dimensions (width_mm, height_mm)
STANDARD_DIMENSIONS: dict[str, tuple[float, float]] = {
    "ISO 7810 ID-1": (85.60, 53.98),
    "Europeu": (85.00, 55.00),
    "EUA / Canadá": (88.90, 50.80),
    "Japonês": (91.00, 55.00),
    "Chinês": (90.00, 54.00),
}

TOLERANCE_MM: float = 0.5


def check_dimensions(file_path: str) -> dict:
    """Check if document dimensions match any standard card format.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Dictionary with check results.
    """
    doc = fitz.open(file_path)
    try:
        page = doc[0]
        rect = page.mediabox
        width_mm = round(rect.width * 25.4 / 72, 2)
        height_mm = round(rect.height * 25.4 / 72, 2)

        matched_standard: Optional[str] = None

        for name, (std_w, std_h) in STANDARD_DIMENSIONS.items():
            # Check both orientations
            if (
                (abs(width_mm - std_w) < TOLERANCE_MM and abs(height_mm - std_h) < TOLERANCE_MM)
                or (abs(width_mm - std_h) < TOLERANCE_MM and abs(height_mm - std_w) < TOLERANCE_MM)
            ):
                matched_standard = name
                break

        if matched_standard:
            return {
                "status": "OK",
                "valor": f"{width_mm} x {height_mm}mm",
                "norma": matched_standard,
                "width_mm": width_mm,
                "height_mm": height_mm,
            }
        else:
            return {
                "status": "ERRO",
                "codigo": "E001_DIMENSION_MISMATCH",
                "valor_encontrado": f"{width_mm} x {height_mm}mm",
                "valor_esperado": "ISO 7810, Europeu, EUA, Japonês ou Chinês",
                "width_mm": width_mm,
                "height_mm": height_mm,
            }
    finally:
        doc.close()

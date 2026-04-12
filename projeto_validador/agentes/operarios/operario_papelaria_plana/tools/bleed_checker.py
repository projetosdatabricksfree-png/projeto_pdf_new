"""
Bleed Checker — Validates bleed (sangria) configuration.

Compares BleedBox vs TrimBox to determine bleed amount.
"""
from __future__ import annotations

import fitz


def check_bleed(file_path: str) -> dict:
    """Check bleed configuration by comparing BleedBox and TrimBox.

    Valid bleed: 2.0mm ≤ bleed ≤ 3.0mm on each side.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Dictionary with check results.
    """
    doc = fitz.open(file_path)
    try:
        page = doc[0]

        bleedbox = page.bleedbox
        trimbox = page.trimbox

        # Calculate bleed in mm on each side
        bleed_left_mm = (trimbox.x0 - bleedbox.x0) * 25.4 / 72
        bleed_right_mm = (bleedbox.x1 - trimbox.x1) * 25.4 / 72
        bleed_top_mm = (trimbox.y0 - bleedbox.y0) * 25.4 / 72
        bleed_bottom_mm = (bleedbox.y1 - trimbox.y1) * 25.4 / 72

        # Use the minimum bleed value for assessment
        min_bleed = min(bleed_left_mm, bleed_right_mm, bleed_top_mm, bleed_bottom_mm)
        max_bleed = max(bleed_left_mm, bleed_right_mm, bleed_top_mm, bleed_bottom_mm)
        avg_bleed = round((bleed_left_mm + bleed_right_mm + bleed_top_mm + bleed_bottom_mm) / 4, 2)

        result: dict = {
            "bleed_left_mm": round(bleed_left_mm, 2),
            "bleed_right_mm": round(bleed_right_mm, 2),
            "bleed_top_mm": round(bleed_top_mm, 2),
            "bleed_bottom_mm": round(bleed_bottom_mm, 2),
            "min_bleed_mm": round(min_bleed, 2),
        }

        # No bleed at all
        if min_bleed <= 0.01:
            result.update({
                "status": "ERRO",
                "codigo": "E002_MISSING_BLEED",
                "valor_encontrado": f"{avg_bleed}mm",
                "valor_esperado": "2-3mm",
            })
            return result

        # Insufficient bleed
        if min_bleed < 2.0:
            result.update({
                "status": "ERRO",
                "codigo": "E003_INSUFFICIENT_BLEED",
                "valor_encontrado": f"{round(min_bleed, 2)}mm",
                "valor_esperado": "≥ 2mm",
            })
            return result

        # Excessive bleed (warning only)
        if max_bleed > 3.0:
            result.update({
                "status": "AVISO",
                "codigo": "W001_EXCESSIVE_BLEED",
                "valor_encontrado": f"{round(max_bleed, 2)}mm",
                "valor_esperado": "≤ 3mm",
            })
            return result

        # Valid bleed
        result.update({
            "status": "OK",
            "valor": f"{avg_bleed}mm",
        })
        return result

    finally:
        doc.close()


def check_safety_margin(file_path: str) -> dict:
    """Check safety margin by comparing ArtBox/CropBox and TrimBox.

    Valid margin: 3.0mm ≤ margin ≤ 5.0mm inside TrimBox.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Dictionary with check results.
    """
    doc = fitz.open(file_path)
    try:
        page = doc[0]
        artbox = page.artbox
        trimbox = page.trimbox

        margin_left = (artbox.x0 - trimbox.x0) * 25.4 / 72
        margin_right = (trimbox.x1 - artbox.x1) * 25.4 / 72
        margin_top = (artbox.y0 - trimbox.y0) * 25.4 / 72
        margin_bottom = (trimbox.y1 - artbox.y1) * 25.4 / 72

        min_margin = min(margin_left, margin_right, margin_top, margin_bottom)

        result: dict = {"min_margin_mm": round(min_margin, 2)}

        if min_margin < 3.0:
            result.update({
                "status": "ERRO",
                "codigo": "E004_INSUFFICIENT_SAFETY_MARGIN",
                "valor_encontrado": f"{round(min_margin, 2)}mm",
                "valor_esperado": "≥ 3mm",
            })
        elif min_margin < 3.5:
            result.update({
                "status": "AVISO",
                "codigo": "W002_TIGHT_SAFETY_MARGIN",
                "valor_encontrado": f"{round(min_margin, 2)}mm",
                "valor_esperado": "≥ 3.5mm ideal",
            })
        else:
            result.update({
                "status": "OK",
                "valor": f"{round(min_margin, 2)}mm",
            })

        return result

    finally:
        doc.close()

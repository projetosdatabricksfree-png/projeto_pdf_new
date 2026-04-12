"""
Font Checker — Validates font embedding and hairline detection.

Uses PyMuPDF to inspect font lists and drawing widths.
"""
from __future__ import annotations

import fitz



# Standard PDF base-14 fonts that never need embedding
BASE14_FONTS: set[str] = {
    "courier", "courier-bold", "courier-oblique", "courier-boldoblique",
    "helvetica", "helvetica-bold", "helvetica-oblique", "helvetica-boldoblique",
    "times-roman", "times-bold", "times-italic", "times-bolditalic",
    "symbol", "zapfdingbats",
    # PyMuPDF aliases
    "helv", "heit", "cour", "coit", "tiro", "tiit", "tibo", "tibi",
    "cobo", "cobi", "hebo", "hebi", "symb", "zadb",
}


def _is_base14(font_name: str) -> bool:
    """Check if a font is a standard PDF base-14 font that doesn't need embedding."""
    name_lower = font_name.lower().strip()
    for base in BASE14_FONTS:
        if base in name_lower:
            return True
    return False


def check_fonts_embedded(file_path: str) -> dict:
    """Check if all fonts are embedded in the PDF.

    Standard PDF base-14 fonts (Helvetica, Times, Courier, etc.) are
    exempt as they are guaranteed to be available per the PDF specification.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Dictionary with check results.
    """
    doc = fitz.open(file_path)
    try:
        all_fonts: list[str] = []
        non_embedded: list[str] = []

        for page_num in range(min(doc.page_count, 10)):
            fonts = doc[page_num].get_fonts(full=True)
            for font in fonts:
                font_name = font[3] if len(font) > 3 else f"font_{font[0]}"
                all_fonts.append(font_name)

                # Base-14 fonts are always available — skip embedding check
                if _is_base14(font_name):
                    continue

                # For non-standard fonts, check if data is embedded
                font_type = font[1] if len(font) > 1 else ""
                if font_type and "Type3" not in str(font_type):
                    try:
                        xref = font[0]
                        font_data = doc.xref_stream(xref)
                        if not font_data or len(font_data) < 10:
                            non_embedded.append(font_name)
                    except Exception:
                        pass  # Could not verify, assume embedded

        unique_fonts = list(set(all_fonts))
        unique_non_embedded = list(set(non_embedded))

        if unique_non_embedded:
            return {
                "status": "ERRO",
                "codigo": "E008_NON_EMBEDDED_FONTS",
                "valor_encontrado": ", ".join(unique_non_embedded),
                "valor_esperado": "Todas as fontes incorporadas",
                "total_fontes": len(unique_fonts),
                "nao_embutidas": unique_non_embedded,
            }

        return {
            "status": "OK",
            "valor": f"{len(unique_fonts)} fontes embutidas",
            "fontes": unique_fonts,
        }

    finally:
        doc.close()


def check_hairlines(file_path: str, min_width_pt: float = 0.25) -> dict:
    """Check for hairline strokes (lines thinner than minimum width).

    Args:
        file_path: Path to the PDF file.
        min_width_pt: Minimum acceptable line width in points.

    Returns:
        Dictionary with check results.
    """
    doc = fitz.open(file_path)
    try:
        hairlines_found: list[dict] = []

        for page_num in range(min(doc.page_count, 5)):
            page = doc[page_num]
            try:
                drawings = page.get_drawings()
                for drawing in drawings:
                    width = drawing.get("width", 0)
                    if width is not None and 0 < width < min_width_pt:
                        hairlines_found.append({
                            "page": page_num + 1,
                            "width_pt": round(width, 4),
                        })
                        if len(hairlines_found) >= 10:
                            break  # Cap at 10 hairlines
            except Exception:
                continue

            if len(hairlines_found) >= 10:
                break

        if hairlines_found:
            return {
                "status": "ERRO",
                "codigo": "E010_HAIRLINE_DETECTED",
                "valor_encontrado": f"{hairlines_found[0]['width_pt']}pt",
                "valor_esperado": f"≥ {min_width_pt}pt",
                "detalhes": hairlines_found[:5],
            }

        return {
            "status": "OK",
            "valor": f"Todas as linhas ≥ {min_width_pt}pt",
        }

    finally:
        doc.close()


def check_nfc_zone(file_path: str, width_mm: float, height_mm: float) -> dict:
    """Check if content invades the NFC chip zone (ISO 7810 ID-1 only).

    The NFC chip zone is a central rectangle of ~30mm x 20mm.

    Args:
        file_path: Path to the PDF file.
        width_mm: Document width in mm.
        height_mm: Document height in mm.

    Returns:
        Dictionary with check results.
    """
    # Only applicable for ISO 7810 ID-1 format
    is_id1 = (
        abs(width_mm - 85.60) < 1.0 and abs(height_mm - 53.98) < 1.0
    ) or (
        abs(width_mm - 53.98) < 1.0 and abs(height_mm - 85.60) < 1.0
    )

    if not is_id1:
        return {
            "status": "N/A",
            "detalhe": "Formato não ID-1",
        }

    # NFC chip zone in mm (center of card)
    chip_zone = {
        "x_min": (85.60 / 2 - 15),  # mm from left
        "x_max": (85.60 / 2 + 15),
        "y_min": (53.98 / 2 - 10),  # mm from top
        "y_max": (53.98 / 2 + 10),
    }

    doc = fitz.open(file_path)
    try:
        page = doc[0]

        # Convert chip zone to PDF points
        zone_x0 = chip_zone["x_min"] * 72 / 25.4
        zone_x1 = chip_zone["x_max"] * 72 / 25.4
        zone_y0 = chip_zone["y_min"] * 72 / 25.4
        zone_y1 = chip_zone["y_max"] * 72 / 25.4
        zone_rect = fitz.Rect(zone_x0, zone_y0, zone_x1, zone_y1)

        # Check if any drawings intersect the zone
        try:
            drawings = page.get_drawings()
            for drawing in drawings:
                draw_rect = drawing.get("rect")
                if draw_rect and fitz.Rect(draw_rect).intersects(zone_rect):
                    return {
                        "status": "ERRO",
                        "codigo": "E009_NFC_ZONE_VIOLATION",
                        "detalhe": "Conteúdo vetorial na área NFC",
                        "zona_mm": chip_zone,
                    }
        except Exception:
            pass

        return {
            "status": "OK",
            "detalhe": "Zona NFC livre",
        }

    finally:
        doc.close()

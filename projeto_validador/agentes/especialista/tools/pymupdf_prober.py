"""
PyMuPDF Prober — Structural analysis of PDFs without rendering pixels.

Samples at most the first 5 pages (Rule: never process all pages).
Uses only page dictionaries, drawings info, and image metadata — NO rasterization.
"""
from __future__ import annotations

import logging
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

MAX_SAMPLE_PAGES: int = 5


def probe_structure(file_path: str) -> dict[str, Any]:
    """Analyze PDF structure without rendering any pixels.

    Extracts page rects, annotations, links, font info, and image counts.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Dictionary with structural probing data.
    """
    doc = fitz.open(file_path)
    try:
        page_count = doc.page_count
        page_rects: list[dict] = []
        total_images = 0
        total_vectors = 0
        has_embedded_fonts = False
        font_names: list[str] = []

        for i in range(min(page_count, MAX_SAMPLE_PAGES)):
            page = doc[i]
            rect = page.mediabox

            page_info = {
                "page": i,
                "width": round(rect.width * 25.4 / 72, 2),
                "height": round(rect.height * 25.4 / 72, 2),
                "rotation": page.rotation,
                "mediabox": [rect.x0, rect.y0, rect.x1, rect.y1],
            }

            # Cropbox and bleedbox
            try:
                page_info["cropbox"] = list(page.cropbox)
            except Exception:
                pass

            try:
                page_info["bleedbox"] = list(page.bleedbox)
            except Exception:
                pass

            # Count images (without loading pixel data)
            try:
                images = page.get_images(full=False)
                page_info["image_count"] = len(images)
                total_images += len(images)
            except Exception:
                page_info["image_count"] = 0

            # Count vector drawings
            try:
                drawings = page.get_drawings()
                page_info["vector_count"] = len(drawings)
                total_vectors += len(drawings)
            except Exception:
                page_info["vector_count"] = 0

            page_rects.append(page_info)

        # Font analysis (from first page)
        try:
            for page_num in range(min(page_count, MAX_SAMPLE_PAGES)):
                fonts = doc[page_num].get_fonts(full=True)
                for font in fonts:
                    font_name = font[3] if len(font) > 3 else "unknown"
                    font_names.append(font_name)
                    # Check embedded flag (index 7 in full font list)
                    if len(font) > 7 and font[7]:
                        has_embedded_fonts = True
        except Exception:
            pass

        return {
            "page_count": page_count,
            "page_rects": page_rects,
            "raster_image_count": total_images,
            "vector_path_count": total_vectors,
            "has_embedded_fonts": has_embedded_fonts,
            "font_names": list(set(font_names)),
            "pages_sampled": min(page_count, MAX_SAMPLE_PAGES),
        }

    finally:
        doc.close()


def detect_spot_colors_pymupdf(file_path: str) -> list[str]:
    """Detect spot color / separation names in the PDF.

    Searches xref objects for Separation/SpotColor references.

    Args:
        file_path: Path to the PDF file.

    Returns:
        List of spot color/separation names found.
    """
    doc = fitz.open(file_path)
    spot_colors: list[str] = []

    try:
        for xref in range(doc.xref_length()):
            try:
                obj = doc.xref_object(xref)
                if "Separation" in obj or "SpotColor" in obj:
                    spot_colors.append(obj[:200])  # Truncate for safety
            except Exception:
                continue
    finally:
        doc.close()

    return spot_colors

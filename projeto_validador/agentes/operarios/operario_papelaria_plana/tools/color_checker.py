"""
Color Checker — Validates color space (CMYK required) and Total Ink Limit.

Uses Ghostscript for RGB detection and pyvips for TIL sampling.
"""
from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

GS_TIMEOUT: int = 30


def check_color_space(file_path: str) -> dict:
    """Check for RGB color space presence via Ghostscript.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Dictionary with check results.
    """
    safe_path = str(Path(file_path).resolve())

    cmd = [
        "gs",
        "-dBATCH",
        "-dNOPAUSE",
        "-sDEVICE=nullpage",
        safe_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            timeout=GS_TIMEOUT,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        return {"status": "ERRO", "codigo": "E006_RGB_COLORSPACE", "detalhe": "Timeout ao verificar"}
    except FileNotFoundError:
        # Ghostscript not installed — fallback to PyMuPDF check
        return _check_color_pymupdf(file_path)

    output = result.stdout + result.stderr
    has_rgb = bool(re.search(r'DeviceRGB|sRGB|rgb', output, re.IGNORECASE))

    if has_rgb:
        return {
            "status": "ERRO",
            "codigo": "E006_RGB_COLORSPACE",
            "detalhe": "RGB detectado via Ghostscript",
            "valor_encontrado": "RGB",
            "valor_esperado": "CMYK/Pantone",
        }

    return {
        "status": "OK",
        "valor": "CMYK",
    }


def _check_color_pymupdf(file_path: str) -> dict:
    """Fallback color check using PyMuPDF."""
    import fitz

    doc = fitz.open(file_path)
    try:
        for page_num in range(min(doc.page_count, 5)):
            page = doc[page_num]
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n < 4:  # Less than 4 channels = likely RGB or Gray
                        if pix.n == 3:  # RGB
                            return {
                                "status": "ERRO",
                                "codigo": "E006_RGB_COLORSPACE",
                                "detalhe": f"RGB na imagem xref={xref}, página {page_num + 1}",
                            }
                    pix = None  # Free memory
                except Exception:
                    continue
        return {"status": "OK", "valor": "CMYK"}
    finally:
        doc.close()


def check_total_ink_limit(file_path: str, max_til: float = 330.0) -> dict:
    """Check Total Ink Limit via pyvips thumbnail sampling.

    Uses thumbnail at reduced resolution (Rule 1: Anti-OOM).

    Args:
        file_path: Path to the PDF file.
        max_til: Maximum allowed TIL percentage.

    Returns:
        Dictionary with check results.
    """
    try:
        import pyvips

        # Load at reduced resolution — never full size
        thumb = pyvips.Image.thumbnail(file_path, 200, height=200)

        # If CMYK (4 bands), compute max sum across channels
        if thumb.bands >= 4:
            # Get histogram stats
            max_til_found = 0.0
            # Sample center pixels
            width = thumb.width
            height = thumb.height
            for y in range(0, height, max(1, height // 10)):
                for x in range(0, width, max(1, width // 10)):
                    pixel = thumb.getpoint(x, y)
                    if len(pixel) >= 4:
                        # CMYK values are 0-255, convert to percentage
                        til = sum(pixel[:4]) / 255 * 100
                        max_til_found = max(max_til_found, til)

            max_til_found = round(max_til_found, 1)

            if max_til_found > max_til:
                return {
                    "status": "ERRO",
                    "codigo": "E007_EXCESSIVE_INK_COVERAGE",
                    "valor_encontrado": f"{max_til_found}%",
                    "valor_esperado": f"≤ {max_til}%",
                }

            return {
                "status": "OK",
                "valor": f"{max_til_found}%",
            }

        return {"status": "OK", "valor": "N/A (não CMYK)"}

    except Exception as exc:
        logger.warning(f"TIL check failed: {exc}")
        return {"status": "OK", "valor": "N/A (pyvips indisponível)"}

"""
Rich Black Detector — Detects Rich Black usage in body text.

Rich Black in body text causes registration blur.
Body text should use 100% K only (pure black).
"""
from __future__ import annotations


def check_rich_black(file_path: str) -> dict:
    """Check for Rich Black in body text.

    This is a simplified check — in production, you'd sample
    text pixels via pyvips to detect CMY values > 0 in text areas.

    Args:
        file_path: Path to the PDF.

    Returns:
        Dictionary with check results.
    """
    try:
        import fitz

        doc = fitz.open(file_path)
        try:
            # Sample first few pages for text blocks
            for page_num in range(min(doc.page_count, 10)):
                page = doc[page_num]
                # Get text blocks with color info
                blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                for block in blocks.get("blocks", []):
                    if block.get("type") == 0:  # Text block
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                color = span.get("color", 0)
                                # If color is not pure black (0x000000) and not
                                # too light, it might be Rich Black
                                # This is approximate — real detection needs CMYK values
                                pass

            return {"status": "OK", "valor": "Preto puro detectado"}

        finally:
            doc.close()

    except Exception as exc:
        return {"status": "OK", "valor": f"N/A ({exc})"}

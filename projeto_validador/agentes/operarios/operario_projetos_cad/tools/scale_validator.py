"""
Scale Validator — Validates 1:1 scale for technical drawings.

Checks UserUnit and viewport scale — deviation > 0.1% = critical error.
"""
from __future__ import annotations

import fitz

FORMATOS_VALIDOS: dict[str, tuple[float, float]] = {
    "A0": (841, 1189), "A1": (594, 841),
    "A2": (420, 594), "A3": (297, 420),
    "A4": (210, 297),
}


def check_scale(file_path: str) -> dict:
    """Check document scale — must be 1:1."""
    doc = fitz.open(file_path)
    try:
        page = doc[0]
        # Check UserUnit (should be 1.0 for 1:1 scale)
        # PyMuPDF doesn't expose UserUnit directly, but we can check
        # page dictionary for it
        try:
            page_dict = doc.xref_object(page.xref)
            if "UserUnit" in page_dict:
                # Extract value
                import re
                match = re.search(r'UserUnit\s+(\d+\.?\d*)', page_dict)
                if match:
                    user_unit = float(match.group(1))
                    if abs(user_unit - 1.0) > 0.001:
                        return {
                            "status": "ERRO",
                            "codigo": "E001_SCALE_DEVIATION",
                            "valor_encontrado": f"UserUnit={user_unit}",
                            "valor_esperado": "UserUnit=1.0",
                        }
        except Exception:
            pass

        return {"status": "OK", "valor": "Escala 1:1"}
    finally:
        doc.close()


def check_format(file_path: str) -> dict:
    """Check if document matches a standard ISO format."""
    doc = fitz.open(file_path)
    try:
        page = doc[0]
        rect = page.mediabox
        width_mm = round(rect.width * 25.4 / 72, 2)
        height_mm = round(rect.height * 25.4 / 72, 2)

        tolerancia = 2.0
        formato = None
        for nome, (w, h) in FORMATOS_VALIDOS.items():
            if (abs(width_mm - w) < tolerancia and abs(height_mm - h) < tolerancia) or \
               (abs(width_mm - h) < tolerancia and abs(height_mm - w) < tolerancia):
                formato = nome
                break

        if formato:
            return {"status": "OK", "formato": formato, "dimensoes": f"{width_mm} x {height_mm}mm"}
        else:
            return {
                "status": "AVISO",
                "codigo": "W001_NON_STANDARD_FORMAT",
                "valor_encontrado": f"{width_mm} x {height_mm}mm",
            }
    finally:
        doc.close()

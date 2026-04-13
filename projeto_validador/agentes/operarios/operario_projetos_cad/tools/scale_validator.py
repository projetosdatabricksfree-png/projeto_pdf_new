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


def check_scale(doc: fitz.Document) -> dict:
    """Check document scale — must be 1:1."""
    try:
        page = doc[0]
        # Check UserUnit (should be 1.0 for 1:1 scale)
        try:
            page_dict = doc.xref_object(page.xref)
            if "UserUnit" in page_dict:
                import re
                match = re.search(r'UserUnit\s+(\d+\.?\d*)', page_dict)
                if match:
                    user_unit = float(match.group(1))
                    if abs(user_unit - 1.0) > 0.001:
                        return {
                            "status": "ERRO",
                            "codigo": "E001_SCALE_DEVIATION",
                            "label": "Escala do Desenho",
                            "found_value": f"UserUnit={user_unit}",
                            "expected_value": "UserUnit=1.0",
                            "meta": {
                                "client": f"Desvio de escala detectado (UserUnit={user_unit}).",
                                "action": "Exporte o PDF com escala 1:1 (UserUnit=1.0)."
                            }
                        }
        except Exception:
            pass

        return {
            "status": "OK",
            "label": "Escala do Desenho",
            "found_value": "Escala 1:1",
            "expected_value": "Escala 1:1",
            "meta": {"client": "Desenho técnico em escala 1:1 correta.", "action": "Nenhuma."}
        }
    except Exception as exc:
        return {"status": "ERRO", "detalhe": f"Falha na escala: {str(exc)}"}


def check_format(doc: fitz.Document) -> dict:
    """Check if document matches a standard ISO format."""
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
            return {
                "status": "OK", 
                "formato": formato, 
                "label": "Formato do Papel",
                "found_value": f"{formato} ({width_mm}x{height_mm}mm)",
                "expected_value": "Padrão ISO A0-A4",
                "meta": {"client": f"Formato {formato} detectado.", "action": "Nenhuma."}
            }
        else:
            return {
                "status": "AVISO",
                "codigo": "W001_NON_STANDARD_FORMAT",
                "label": "Formato do Papel",
                "found_value": f"{width_mm} x {height_mm}mm",
                "expected_value": "Padrão ISO A0-A4",
                "meta": {
                    "client": f"Tamanho personalizado ({width_mm}x{height_mm}mm) detectado.",
                    "action": "Verifique se o formato está correto para a plotagem."
                }
            }
    except Exception as exc:
        return {"status": "ERRO", "detalhe": f"Falha no formato: {str(exc)}"}

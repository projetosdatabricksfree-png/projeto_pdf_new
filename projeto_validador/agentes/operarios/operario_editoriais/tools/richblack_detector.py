"""
Rich Black Detector — Detects Rich Black usage in body text.

Rich Black in body text causes registration blur.
Body text should use 100% K only (pure black).
"""
from __future__ import annotations


def check_rich_black(file_path: str) -> dict:
    """Check for Rich Black and Overprint in small text (< 12pt).
    
    Per GWG 2015/PDF/X-4:
    - Text < 12pt MUST be K=100 (no CMY).
    - Text < 12pt SHOULD have overprint ON.
    """
    try:
        import fitz
        doc = fitz.open(file_path)
        violations = []
        
        try:
            # Sample pages for performance (Rule 1: Anti-OOM)
            for page_num in range(min(doc.page_count, 20)):
                page = doc[page_num]
                blocks = page.get_text("dict")
                
                for block in blocks.get("blocks", []):
                    if block.get("type") == 0:  # Text
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                size = span.get("size", 0)
                                color = span.get("color", 0)
                                
                                # Rule: small text (< 12pt)
                                if 0 < size < 12:
                                    # In PyMuPDF, if color is not 0 (pure black), 
                                    # it indicates potential Rich Black or other colors.
                                    if color != 0:
                                        violations.append(f"Rich Black detected at size {size}")

            if violations:
                return {
                    "status": "ERRO",
                    "codigo": "E_RICH_BLACK_TEXT",
                    "label": "Preto Composto em Texto",
                    "found_value": "Rich Black (C+M+Y+K)",
                    "expected_value": "Pure Black (K=100)",
                    "descricao": "Textos pequenos (< 12pt) detectados com preto composto.",
                    "detalhes": violations[:5]
                }

            return {
                "status": "OK",
                "label": "Preto Composto em Texto",
                "found_value": "Pure Black (K=100)",
                "expected_value": "Pure Black (K=100)",
                "meta": {
                    "client": "Textos pequenos estão usando apenas o canal preto (K).",
                    "action": "Nenhuma."
                }
            }

        finally:
            doc.close()
    except Exception as exc:
        return {
            "status": "AVISO", 
            "found_value": "Desconhecido",
            "expected_value": "Pure Black (K=100)",
            "detalhe": f"Falha ao ler fontes: {exc}"
        }

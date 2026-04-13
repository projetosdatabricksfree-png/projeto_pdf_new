"""
GWG Geometry Checker - Ghent Workgroup 2015/2022
Validates PDF Page Boxes (TrimBox, BleedBox, MediaBox) and Bleed margins.
"""

import fitz
from typing import Dict, Any, List

def gwg_round(value: float, precision: int = 2) -> float:
    """Arredonda valores seguindo a lógica GWG para evitar imprecisão de float."""
    return round(value, precision)

def is_within_tolerance(val1: float, val2: float, tolerance: float = 0.011) -> bool:
    """Verifica se dois valores estão dentro da tolerância GWG (±0.01mm)."""
    return abs(val1 - val2) <= tolerance

def check_geometry(doc_path: str) -> List[Dict[str, Any]]:
    """
    Analisa a geometria de todas as páginas do PDF com tolerância GWG.
    """
    doc = fitz.open(doc_path)
    results = []
    
    # 72 points per inch (standard PDF unit)
    # 1 mm = 2.83465 points
    PX_TO_MM = 0.352778

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_checks = []
        
        # Obter boxes
        mediabox = page.mediabox
        trimbox = page.trimbox
        bleedbox = page.bleedbox
        
        # 1. Verificar se TrimBox está definida
        # Usamos is_within_tolerance para evitar erros de arredondamento biário
        is_same_as_media = is_within_tolerance(trimbox.width, mediabox.width) and \
                           is_within_tolerance(trimbox.height, mediabox.height)
        
        if is_same_as_media:
            page_checks.append({
                "code": "G001",
                "label": "Definição de TrimBox",
                "status": "AVISO",
                "found_value": "Não definida explicitamente",
                "expected_value": "TrimBox separada da MediaBox",
                "meta": {
                    "client": "O tamanho final do material não foi definido corretamente no arquivo.",
                    "action": "Defina o formato final (Corte) no seu software de diagramação."
                }
            })
        else:
            page_checks.append({
                "code": "G001",
                "label": "Definição de TrimBox",
                "status": "OK",
                "found_value": f"{gwg_round(trimbox.width * PX_TO_MM)}x{gwg_round(trimbox.height * PX_TO_MM)}mm",
                "expected_value": "TrimBox Identificada",
                "meta": {"client": "Formato final identificado corretamente.", "action": "Nenhuma."}
            })

        # 2. Verificar Sangria (Bleed)
        # BleedBox deve ser maior que TrimBox
        bleed_top = (trimbox.y0 - bleedbox.y0) * PX_TO_MM
        bleed_bottom = (bleedbox.y1 - trimbox.y1) * PX_TO_MM
        bleed_left = (trimbox.x0 - bleedbox.x0) * PX_TO_MM
        bleed_right = (bleedbox.x1 - trimbox.x1) * PX_TO_MM
        
        min_bleed = min(bleed_top, bleed_bottom, bleed_left, bleed_right)
        
        # Tolerância GWG: Se o valor for 2.99mm e o esperado é 3mm, aceitamos
        if min_bleed < 2.99: 
            page_checks.append({
                "code": "G002",
                "label": "Margem de Sangria",
                "status": "ERRO" if min_bleed <= 0.01 else "AVISO",
                "found_value": f"{gwg_round(min_bleed)}mm",
                "expected_value": ">= 3.00mm",
                "meta": {
                    "client": f"A sangria detectada ({gwg_round(min_bleed)}mm) é insuficiente.",
                    "action": "Aumente a sangria para pelo menos 3mm em todos os lados (Tolerância ±0.01mm aplicada)."
                }
            })
        else:
            page_checks.append({
                "code": "G002",
                "label": "Margem de Sangria",
                "status": "OK",
                "found_value": f"{round(min_bleed, 2)}mm",
                "expected_value": ">= 3.00mm",
                "meta": {"client": "Sangria adequada para produção.", "action": "Nenhuma."}
            })

        results.append({
            "page": page_index + 1,
            "checks": page_checks
        })
        
    doc.close()
    return results

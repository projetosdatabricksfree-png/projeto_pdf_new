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

def check_geometry(doc_path: str, profile: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Analisa a geometria de todas as páginas do PDF seguindo GWG 2015 (§4.2 a 4.6).
    """
    doc = fitz.open(doc_path)
    results = []
    profile = profile or {}
    profile_name = profile.get("name", "")
    
    # 72 points per inch (standard PDF unit)
    # 1 mm = 2.83465 points
    PX_TO_MM = 0.352778
    
    # Track first page dimensions for uniformity check (GE-03)
    first_trimbox = None
    
    # GE-05: Page Count
    page_count = len(doc)
    # Match strings like "Magazine Ads" or "MagazineAds"
    is_ad = any(k in profile_name for k in ["Magazine", "Newspaper"]) and "Ads" in profile_name
    
    if is_ad and page_count > 1:
        # We add this to the first page results for now
        pass 

    for page_index in range(page_count):
        page = doc[page_index]
        page_checks = []
        
        # Obter boxes
        mediabox = page.mediabox
        trimbox = page.trimbox
        bleedbox = page.bleedbox
        cropbox = page.cropbox # Standard PDF CropBox
        
        # ─── GE-01: Page Scaling (UserUnit) ───────────────────────
        # O dicionário da página não deve conter a chave UserUnit
        user_unit = page.parent.xref_get_key(page.xref, "UserUnit")
        if user_unit[0] != "null":
            page_checks.append({
                "code": "GE-01",
                "label": "Page Scaling (UserUnit)",
                "status": "ERRO",
                "found_value": f"UserUnit = {user_unit[1]}",
                "expected_value": "Ausência de UserUnit",
                "meta": {
                    "client": "O arquivo contém fator de escala personalizado (UserUnit).",
                    "action": "Desative o dimensionamento de página não-padrão ao exportar."
                }
            })

        # ─── GE-02: Crop Box ──────────────────────────────────────
        # Se CropBox presente, deve ser igual a MediaBox
        # Note: No PyMuPDF, page.cropbox sempre retorna algo. 
        # Verificamos se ele difere do MediaBox de forma relevante.
        if not is_within_tolerance(cropbox.width, mediabox.width) or \
           not is_within_tolerance(cropbox.height, mediabox.height):
             page_checks.append({
                "code": "GE-02",
                "label": "Crop Box",
                "status": "ERRO",
                "found_value": f"CropBox {gwg_round(cropbox.width*PX_TO_MM)}x{gwg_round(cropbox.height*PX_TO_MM)}mm",
                "expected_value": f"Mesmo que MediaBox ({gwg_round(mediabox.width*PX_TO_MM)}mm)",
                "meta": {
                    "client": "CropBox detectada com tamanho diferente da MediaBox.",
                    "action": "Configure CropBox == MediaBox ou remova a CropBox."
                }
            })

        # ─── GE-03: Uniformity & Rotate ───────────────────────────
        # Rotate deve ser 0
        rotation = page.rotation
        if rotation != 0:
            page_checks.append({
                "code": "GE-03",
                "label": "Page Rotation",
                "status": "AVISO",
                "found_value": f"Rotate = {rotation}",
                "expected_value": "Rotate = 0",
                "meta": {
                    "client": "A página possui um atributo de rotação.",
                    "action": "Aqueça o PDF ou remova a rotação lógica, mantendo a orientação na geometria."
                }
            })
            
        # TrimBox idêntica
        if page_index == 0:
            first_trimbox = trimbox
        else:
            if not is_within_tolerance(trimbox.width, first_trimbox.width) or \
               not is_within_tolerance(trimbox.height, first_trimbox.height):
                page_checks.append({
                    "code": "GE-03",
                    "label": "Uniformidade de TrimBox",
                    "status": "ERRO",
                    "found_value": f"Pág. {page_index+1} difere da Pág. 1",
                    "expected_value": "Dimensões idênticas em todas as páginas",
                    "meta": {
                        "client": "As páginas possuem tamanhos de corte diferentes.",
                        "action": "Padronize o tamanho das páginas no documento original."
                    }
                })

        # ─── G001: Definição de TrimBox (Existente) ───────────────
        is_same_as_media = is_within_tolerance(trimbox.width, mediabox.width) and \
                           is_within_tolerance(trimbox.height, mediabox.height)
        
        if is_same_as_media:
            page_checks.append({
                "code": "G001",
                "label": "Definição de TrimBox",
                "status": "AVISO",
                "found_value": "Não definida",
                "expected_value": "TrimBox definida",
                "meta": {"client": "TrimBox não identificada.", "action": "Defina o formato de corte."}
            })

        # ─── GE-04: Empty Pages ───────────────────────────────────
        # Verificar se há conteúdo visível (vetor ou raster)
        # Uma forma simples é verificar se o display-list tem algum item.
        if page.get_text("words") == [] and page.get_images() == [] and page.get_drawings() == []:
            page_checks.append({
                "code": "GE-04",
                "label": "Página Vazia",
                "status": "AVISO",
                "found_value": "Nenhum conteúdo gráfico detectado",
                "expected_value": "Página com conteúdo",
                "meta": {"client": "Esta página parece não conter elementos gráficos.", "action": "Verifique se a página deve ser removida."}
            })

        # ─── G002: Sangria (Existente) ────────────────────────────
        bleed_top = (trimbox.y0 - bleedbox.y0) * PX_TO_MM
        bleed_bottom = (bleedbox.y1 - trimbox.y1) * PX_TO_MM
        bleed_left = (trimbox.x0 - bleedbox.x0) * PX_TO_MM
        bleed_right = (bleedbox.x1 - trimbox.x1) * PX_TO_MM
        min_bleed = min(bleed_top, bleed_bottom, bleed_left, bleed_right)
        
        if min_bleed < 2.99: 
            page_checks.append({
                "code": "G002",
                "label": "Margem de Sangria",
                "status": "ERRO" if min_bleed <= 0.01 else "AVISO",
                "found_value": f"{gwg_round(min_bleed)}mm",
                "expected_value": ">= 3.00mm"
            })

        # ─── GE-05: Page Count ────────────────────────────────────
        if is_ad and page_index == 0 and page_count > 1:
            page_checks.append({
                "code": "GE-05",
                "label": "Contagem de Páginas (Ads)",
                "status": "ERRO",
                "found_value": f"{page_count} páginas",
                "expected_value": "1 página",
                "meta": {
                    "client": "Anúncios de Revista/Jornal devem conter apenas uma página por PDF.",
                    "action": "Separe as páginas em arquivos individuais."
                }
            })

        results.append({
            "page": page_index + 1,
            "checks": page_checks
        })
        
    doc.close()
    return results

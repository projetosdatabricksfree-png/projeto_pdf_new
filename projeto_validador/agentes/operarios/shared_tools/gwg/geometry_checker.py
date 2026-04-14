"""
GWG Geometry Checker - Ghent Workgroup 2015/2022
Validates PDF Page Boxes (TrimBox, BleedBox, MediaBox) and Bleed margins.
"""

import fitz
import logging
from typing import Dict, Any, List
from .oc_filter import VisibilityFilter, NULL_FILTER
from .error_messages import get_human_error

logger = logging.getLogger(__name__)

def gwg_round(value: float, precision: int = 2) -> float:
    """Arredonda valores seguindo a lógica GWG para evitar imprecisão de float."""
    return round(value, precision)

def is_within_tolerance(val1: float, val2: float, tolerance: float = 0.011) -> bool:
    """Verifica se dois valores estão dentro da tolerância GWG (±0.01mm)."""
    return abs(val1 - val2) <= tolerance

def check_geometry(doc_path: str, profile: Dict[str, Any] = None, visible_filter: VisibilityFilter = NULL_FILTER) -> List[Dict[str, Any]]:
    """
    Analisa a geometria de todas as páginas do PDF seguindo GWG 2015 (§4.2 a 4.6).
    """
    doc = fitz.open(doc_path)
    results = []
    profile = profile or {}
    profile_name = profile.get("name", "")
    
    PX_TO_MM = 0.352778
    
    # Track first page dimensions for uniformity check (GE-03)
    first_trimbox = None
    
    # GE-05: Page Count
    page_count = len(doc)
    # Match strings like "Magazine Ads" or "MagazineAds"
    is_ad = any(k in profile_name for k in ["Magazine", "Newspaper"]) and "Ads" in profile_name

    for page_index in range(page_count):
        page = doc[page_index]
        page_checks = []
        
        # Obter boxes
        mediabox = page.mediabox
        trimbox = page.trimbox
        bleedbox = page.bleedbox
        cropbox = page.cropbox 
        
        # ─── GE-01: Page Scaling (UserUnit) ───────────────────────
        user_unit = page.parent.xref_get_key(page.xref, "UserUnit")
        if user_unit[0] != "null":
            res = {
                "code": "GE-01",
                "label": "Page Scaling (UserUnit)",
                "status": "ERRO",
                "found_value": f"UserUnit = {user_unit[1]}",
                "expected_value": "Ausência de UserUnit"
            }
            res.update(get_human_error(res["code"], res["found_value"], res["expected_value"]))
            page_checks.append(res)

        # ─── GE-02: Crop Box (§4.3) ────────────────────────────────
        # CropBox deve ser igual a MediaBox dentro da tolerância.
        if not is_within_tolerance(cropbox.width, mediabox.width) or \
           not is_within_tolerance(cropbox.height, mediabox.height):
             res = {
                "code": "E_CROPBOX_NEQ_MEDIABOX",
                "label": "Crop Box",
                "status": "ERRO",
                "found_value": f"Δ {gwg_round(abs(cropbox.width-mediabox.width)*PX_TO_MM)}mm",
                "expected_value": "≤ 0.011mm"
            }
             res.update(get_human_error(res["code"], res["found_value"], res["expected_value"]))
             page_checks.append(res)

        # ─── GE-03: Uniformity & Rotate (§4.4 / §4.5) ──────────────
        rotation = page.rotation
        if rotation != 0:
            res = {
                "code": "E_PAGE_ROTATED",
                "label": "Page Rotation",
                "status": "ERRO",
                "found_value": f"Rotate = {rotation}",
                "expected_value": "Rotate = 0"
            }
            res.update(get_human_error(res["code"], res["found_value"], res["expected_value"]))
            page_checks.append(res)
            
        if page_index == 0:
            first_trimbox = trimbox
        else:
            if not is_within_tolerance(trimbox.width, first_trimbox.width) or \
               not is_within_tolerance(trimbox.height, first_trimbox.height):
                res = {
                    "code": "E_TRIMBOX_INCONSISTENT",
                    "label": "Uniformidade de TrimBox",
                    "status": "ERRO",
                    "found_value": f"Pág. {page_index+1}",
                    "expected_value": "Idêntica à Pág. 1"
                }
                res.update(get_human_error(res["code"], res["found_value"], res["expected_value"]))
                page_checks.append(res)

        # ─── G001: Definição de TrimBox ───────────────────────────
        is_same_as_media = is_within_tolerance(trimbox.width, mediabox.width) and \
                           is_within_tolerance(trimbox.height, mediabox.height)
        if is_same_as_media:
            page_checks.append({
                "code": "G001",
                "label": "Definição de TrimBox",
                "status": "AVISO",
                "found_value": "Não definida",
                "expected_value": "TrimBox definida",
                "message": "TrimBox não identificada ou igual à MediaBox.",
                "action": "Defina o formato de corte explicitamente."
            })

        # ─── GE-04: Empty Pages (§4.6) ───────────────────────────
        # Híbrida: Walker -> Renderização
        visible_text = page.get_text("words")
        visible_imgs = page.get_images()
        visible_drawings = [d for d in page.get_drawings() if visible_filter.is_visible(d.get("oc", []))]

        is_blank = False
        if not visible_text and not visible_imgs and not visible_drawings:
            # Prova final: Renderização 24 DPI (Cascata Híbrida)
            pix = page.get_pixmap(dpi=24)
            # Se for CMYK, os 4 canais somados devem ser > 0 para haver conteúdo
            # PyMuPDF renders as RGB by default if CS not specified
            if pix.is_grayscale:
                is_blank = pix.samples.count(b'\xff') == len(pix.samples)
            else:
                # white in RGB is (255, 255, 255)
                # white in CMYK is (0, 0, 0, 0) - but PyMuPDF renders RGB unless requested
                is_blank = all(s == 255 for s in pix.samples)

        if is_blank:
            res = {
                "code": "W_EMPTY_PAGE",
                "label": "Página Vazia",
                "status": "AVISO",
                "found_value": f"Página {page_index+1}",
                "expected_value": "Conteúdo gráfico"
            }
            res.update(get_human_error(res["code"], res["found_value"], res["expected_value"]))
            page_checks.append(res)

        # ─── G002: Sangria ──────────────────────────────────────
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

        # ─── GE-05: Page Count (§4.7 / §5.1) ──────────────────────
        if is_ad and page_index == 0 and page_count > 1:
            res = {
                "code": "E_PAGE_COUNT_INVALID",
                "label": "Contagem de Páginas (Ads)",
                "status": "ERRO",
                "found_value": str(page_count),
                "expected_value": "1"
            }
            res.update(get_human_error(res["code"], res["found_value"], res["expected_value"]))
            page_checks.append(res)

        results.append({
            "page": page_index + 1,
            "checks": page_checks
        })
        
    doc.close()
    return results

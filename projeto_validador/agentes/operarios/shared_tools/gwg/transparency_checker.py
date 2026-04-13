"""
GWG 2022 Compliance - Transparency Checker Tool.
Detects live transparency (Group XObjects, BM entries, Soft Masks) in PDF.
"""
from __future__ import annotations

import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

def check_transparency_gwg(file_path: str) -> dict:
    """
    Scans the PDF for live transparency features.
    GWG 2022 Level 1 (PDF/X-1a based) forbids transparency.
    GWG 2022 Level 2 (PDF/X-4 based) allows it.
    """
    doc = fitz.open(file_path)
    try:
        has_transparency = False
        details = []

        for page_num in range(doc.page_count):
            page = doc[page_num]
            
            # 1. Check for Transparency Groups in Page resources
            if page.xref:
                page_obj = doc.xref_object(page.xref)
                if "/Group" in page_obj and "/Transparency" in page_obj:
                    has_transparency = True
                    details.append(f"Transparency Group found on page {page_num + 1}")

            # 2. Check for Soft Masks (SMask) in images or graphics
            # (Scanning xrefs is more thorough)
        
        # Thorough xref scan for SMask
        total_xrefs = doc.xref_length()
        for xref in range(1, min(total_xrefs, 2000)):
            try:
                obj_str = doc.xref_object(xref)
                if "/SMask" in obj_str:
                    has_transparency = True
                    details.append(f"Soft Mask (SMask) found in xref {xref}")
                    break
                if "/BM" in obj_str and "/Normal" not in obj_str:
                    # Blend modes other than Normal indicate transparency
                    has_transparency = True
                    details.append(f"Blend Mode (BM) found in xref {xref}")
                    break
            except Exception:
                continue
                
        if has_transparency:
            return {
                "status": "AVISO", # Usually allowed in L2, but flagged for L1
                "codigo": "W_TRANSPARENCY_DETECTED",
                "detalhe": "Transparência ativa detectada no arquivo.",
                "transparency_found": True,
                "locations": details[:3]
            }

        return {"status": "OK", "transparency_found": False}
        
    finally:
        doc.close()

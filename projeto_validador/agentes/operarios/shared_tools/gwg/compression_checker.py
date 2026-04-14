"""
Compression Checker — GWG §4.28 and Ghent 17.0 compliance.

Validates:
- IM-03: JPEG2000 (/JPXDecode) usage. In PDF/X-4:2010 (Classic), JP2 is prohibited
  if the bit depth > 8 or advanced features are used. GWG typically discourages it.
- IM-05: JBIG2 detection (Warning for legacy RIPs).
- IM-06: 16-bit image detection (Warning for limited support).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List
import fitz
from .error_messages import get_human_error

logger = logging.getLogger(__name__)

def check_compression_gwg(file_path: str, profile: dict | None = None) -> List[Dict[str, Any]]:
    """
    Check image compression and encoding per GWG/Ghent requirements.
    """
    doc = fitz.open(file_path)
    page_results = []
    
    try:
        seen_xrefs = set()
        for page in doc:
            issues = []
            for img in page.get_images(full=True):
                xref = img[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                
                # Structural check via xref object
                obj = doc.xref_object(xref)
                
                # IM-03: JPEG2000
                if "/JPXDecode" in obj:
                    # In many GWG profiles for CMYK delivery, JPX is prohibited
                    issues.append({
                        "code": "E_JPEG2000_FORBIDDEN",
                        "label": "Compressão JPEG2000",
                        "status": "ERRO",
                        "found_value": "/JPXDecode",
                        "expected_value": "/DCTDecode (JPEG) ou /FlateDecode"
                    })
                
                # IM-05: JBIG2
                if "/JBIG2Decode" in obj:
                    issues.append({
                        "code": "W_JBIG2_LEGACY",
                        "label": "Compressão JBIG2",
                        "status": "AVISO",
                        "found_value": "/JBIG2Decode",
                        "expected_value": "/CCITTFaxDecode"
                    })
                
                # IM-06: 16-bit detection
                if "/BitsPerComponent 16" in obj:
                    issues.append({
                        "code": "W_IMAGE_16BIT",
                        "label": "Imagens 16-bit",
                        "status": "AVISO",
                        "found_value": "16-bit",
                        "expected_value": "8-bit"
                    })

            if issues:
                for issue in issues:
                    issue.update(get_human_error(issue["code"], issue["found_value"], issue["expected_value"]))
                
                page_results.append({
                    "page": page.number + 1,
                    "checks": issues
                })

        return page_results

    finally:
        doc.close()

"""
ICC Checker — GWG §4.30 and Ghent 13.x/20.x compliance.

Validates:
- IC-04: OutputIntent.DestOutputProfile presence and validity (CMYK v2/v4).
- IC-05: Multiple OutputIntents must be byte-identical (SHA256).
- IC-02: Profile CS must be CMYK.
"""
from __future__ import annotations

import logging
import hashlib
from typing import Any, Dict, List
import fitz
from .error_messages import get_human_error

logger = logging.getLogger(__name__)

def _get_icc_info(profile_data: bytes) -> Dict[str, Any]:
    """Basic ICC header parser (128 bytes)."""
    if len(profile_data) < 128:
        return {"valid": False, "error": "Profile too small"}
        
    # Bytes 16-19: Color Space of Data (e.g. 'CMYK', 'RGB ')
    cs = profile_data[16:20].decode("ascii", errors="ignore").strip()
    
    # Bytes 8-11: ICC Version (Major.Minor.Bugfix)
    version = f"{profile_data[8]}.{profile_data[9] >> 4}"
    
    return {
        "valid": True,
        "cs": cs,
        "version": version,
        "size": len(profile_data),
        "hash": hashlib.sha256(profile_data).hexdigest()
    }

def check_icc_compliance(file_path: str, profile: dict | None = None) -> List[Dict[str, Any]]:
    """
    Validate OutputIntent ICC profiles per §4.30.
    """
    doc = fitz.open(file_path)
    page_results = []
    
    try:
        # PDF/X-4 usually has OutputIntents in the Catalog
        catalog_xref = doc.pdf_catalog()
        if not catalog_xref:
            return []
            
        doc.xref_object(catalog_xref)
        # Look for /OutputIntents [ ... ]
        doc.get_sig_flags() # PyMuPDF has specific methods, but checking refs is safer for raw ICC
        
        # Cross-reference all OutputIntent profiles
        profiles_info = []
        for xref in range(1, doc.xref_length()):
            try:
                obj = doc.xref_object(xref)
                if '/OutputIntent' in obj and '/DestOutputProfile' in obj:
                    import re
                    prof_m = re.search(r'/DestOutputProfile\s+(\d+)\s+0\s+R', obj)
                    if prof_m:
                        prof_xref = int(prof_m.group(1))
                        data = doc.xref_stream(prof_xref)
                        if data:
                            profiles_info.append({
                                "xref": prof_xref,
                                **_get_icc_info(data)
                            })
            except Exception:
                continue

        issues = []
        
        # IC-01: At least one OutputIntent
        if not profiles_info:
             issues.append({
                "code": "E_OUTPUTINTENT_MISSING",
                "label": "OutputIntent ICC",
                "status": "ERRO",
                "found_value": "Nenhum",
                "expected_value": "Perfil CMYK incorporado"
            })
        else:
            # IC-05: Multiple OutputIntents must be identical
            hashes = {p["hash"] for p in profiles_info}
            if len(hashes) > 1:
                issues.append({
                    "code": "E_OUTPUTINTENT_DIVERGENT",
                    "label": "Múltiplos Perfis de Saída",
                    "status": "ERRO",
                    "found_value": f"{len(hashes)} perfis diferentes",
                    "expected_value": "Perfil único e idêntico"
                })
            
            # IC-02/IC-04: Per-profile validation
            for p in profiles_info:
                if not p["valid"]:
                    issues.append({
                        "code": "E_OUTPUTINTENT_INVALID",
                        "label": "Integridade do Perfil ICC",
                        "status": "ERRO",
                        "found_value": p.get("error", "Corrompido"),
                        "expected_value": "Valid ICC Profile"
                    })
                elif p["cs"] != "CMYK":
                    issues.append({
                        "code": "E_OUTPUTINTENT_NOT_CMYK",
                        "label": "Espaço de Cor do Perfil",
                        "status": "ERRO",
                        "found_value": p["cs"],
                        "expected_value": "CMYK"
                    })
                
                # IC-03: Warning for ICC v4 (Ghent 20.x)
                if p["version"].startswith("4"):
                    issues.append({
                        "code": "W_ICC_V4",
                        "label": "Versão do Perfil ICC",
                        "status": "AVISO",
                        "found_value": "ICC v4",
                        "expected_value": "ICC v2 (Recomendado)"
                    })

        if issues:
            for issue in issues:
                issue.update(get_human_error(issue["code"], issue["found_value"], issue["expected_value"]))
            
            page_results.append({
                "page": 1,
                "checks": issues
            })

        return page_results

    finally:
        doc.close()

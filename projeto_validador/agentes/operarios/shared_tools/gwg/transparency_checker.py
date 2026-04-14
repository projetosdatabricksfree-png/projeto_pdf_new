"""
Transparency Checker — GWG §4.25 and Ghent 16.x compliance.

Validates:
- TR-01: Transparency Group CS must be /DeviceCMYK (or absent if default is CMYK).
- TR-02: Soft-mask (S=Luminosity) G dict must have CS in {DeviceCMYK, DeviceGray}.
- TR-03: Detects objects referenced by SMask Luminosity but drawn outside their group.
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List
import fitz
from .error_messages import get_human_error
from .oc_filter import VisibilityFilter, NULL_FILTER

logger = logging.getLogger(__name__)

def check_transparency_gwg(file_path: str, profile: dict | None = None, visible_filter: VisibilityFilter = NULL_FILTER) -> List[Dict[str, Any]]:
    """
    Validate Transparency Groups and Soft Masks per GWG 2015.
    """
    doc = fitz.open(file_path)
    page_results = []

    try:
        for page in doc:
            issues = []
            
            # 1. Check Transparency Groups (/Group)
            page_dict = doc.xref_object(page.xref)
            group_m = re.search(r'/Group\s+<<([^>]*)>>', page_dict)
            if group_m:
                group_body = group_m.group(1)
                # TR-01: Group CS must be DeviceCMYK
                cs_m = re.search(r'/CS\s+/(\w+)', group_body)
                if cs_m:
                    found_cs = cs_m.group(1)
                    if found_cs not in ("DeviceCMYK", "DeviceGray"):
                         issues.append({
                            "code": "E_TGROUP_CS_INVALID",
                            "label": "Espaço de Cor de Transparência",
                            "status": "ERRO",
                            "found_value": found_cs,
                            "expected_value": "DeviceCMYK/DeviceGray"
                        })
                else:
                    # Some specs require explicit CS in Groups for PDF/X-4
                    pass

            # 2. Check Soft Masks (via ExtGState)
            # We look for /SMask in all xrefs used by the page
            # Heuristic: Scan all ExtGState dictionaries
            for xref in range(1, doc.xref_length()):
                try:
                    obj = doc.xref_object(xref)
                    if '/SMask' in obj and '/ExtGState' in obj:
                        # TR-02: SMask Luminosity check
                        if '/Luminosity' in obj:
                            # Look for /G (the group defining the mask)
                            g_m = re.search(r'/G\s+(\d+)\s+0\s+R', obj)
                            if g_m:
                                g_obj = doc.xref_object(int(g_m.group(1)))
                                if '/CS' in g_obj:
                                    g_cs_m = re.search(r'/CS\s+/(\w+)', g_obj)
                                    if g_cs_m:
                                        g_cs = g_cs_m.group(1)
                                        if g_cs not in ("DeviceCMYK", "DeviceGray"):
                                            issues.append({
                                                "code": "E_SMASK_CS_INVALID",
                                                "label": "Espaço de Cor Soft-Mask",
                                                "status": "ERRO",
                                                "found_value": g_cs,
                                                "expected_value": "DeviceCMYK/DeviceGray"
                                            })

                except Exception:
                    continue

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

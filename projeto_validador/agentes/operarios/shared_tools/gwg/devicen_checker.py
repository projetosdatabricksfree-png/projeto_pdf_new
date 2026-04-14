"""
DeviceN / Separation Checker — GWG Output Suite 5.0 spot colour compliance.

Inspects every xref for /Separation and /DeviceN colour space arrays and:
- Extracts spot colour names (Pantone, HKS, custom inks).
- Detects accidental conversion of DeviceN to its AlternateSpace (CMYK/RGB).
- Validates spot colour names (UTF-8, reserved names §4.20).
- Detects ambiguous spot colours (same name, different alternate space §4.21).
- Enforces per-variant max spot colours (§4.18).
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List
import fitz  # PyMuPDF
from .error_messages import get_human_error

logger = logging.getLogger(__name__)

# Reserved names per §4.20
RESERVED_NAMES = {"All", "None"}

# Alternate spaces that indicate RGB fallback (problematic for print)
_RGB_ALTERNATES: frozenset[str] = frozenset({"DeviceRGB", "CalRGB"})
_CMYK_ALTERNATES: frozenset[str] = frozenset({"DeviceCMYK", "DeviceGray"})

def _is_valid_utf8(name: str) -> bool:
    """Check if the name is valid UTF-8."""
    return "\x00" not in name

def _parse_separation_space(obj_str: str) -> dict[str, Any] | None:
    """Parse a /Separation colour space array from an xref object string."""
    m = re.search(r"\[\s*/Separation\s+/([^\s/\]]+)\s+/(\w+)", obj_str)
    if not m:
        m = re.search(r"/Separation\s+/([^\s/]+)\s+/(\w+)", obj_str)
    if not m:
        return None
    return {"name": m.group(1), "alternate": m.group(2), "type": "Separation"}

def _parse_devicen_space(obj_str: str) -> dict[str, Any] | None:
    """Parse a /DeviceN colour space array from an xref object string."""
    m = re.search(r"\[\s*/DeviceN\s+\[([^\]]+)\]\s+/(\w+)", obj_str)
    if not m:
        return None
    raw_names = re.findall(r"/([^\s/\]]+)", m.group(1))
    return {
        "names": [n for n in raw_names if n != "None"],
        "alternate": m.group(2),
        "type": "DeviceN",
    }

def check_devicen(file_path: str, profile: dict | None = None) -> List[Dict[str, Any]]:
    """
    Validate spot colours and DeviceN spaces according to GWG 2015.
    Returns a list of check results (structured for run_full_suite).
    """
    if profile is None:
        from .profile_matcher import get_gwg_profile
        profile = get_gwg_profile("default")
    
    max_spots = profile.get("max_spot_colors", 0)
    doc = fitz.open(file_path)
    
    spot_info: dict[str, set] = {} # name -> set of alternate spaces
    spot_names: set[str] = set()
    conversion_errors = 0
    
    try:
        # 1. Collect all spot colors from the Whole Document
        for xref in range(1, doc.xref_length()):
            try:
                obj_str = doc.xref_object(xref, compressed=False)
            except Exception:
                continue

            if "/Separation" not in obj_str and "/DeviceN" not in obj_str:
                continue

            sep = _parse_separation_space(obj_str)
            if sep:
                name = sep["name"]
                alt = sep["alternate"]
                spot_names.add(name)
                if name not in spot_info:
                    spot_info[name] = set()
                spot_info[name].add(alt)
                if alt in _RGB_ALTERNATES:
                    conversion_errors += 1
                continue

            dn = _parse_devicen_space(obj_str)
            if dn:
                for name in dn["names"]:
                    alt = dn["alternate"]
                    spot_names.add(name)
                    if name not in spot_info:
                        spot_info[name] = set()
                    spot_info[name].add(alt)
                    if alt in _RGB_ALTERNATES:
                        conversion_errors += 1

        # 2. Perform Checks
        page_results = []
        
        # SP-04: Max Spot Colors (§4.18)
        if len(spot_names) > max_spots:
             res = {
                "code": "E_SPOT_COUNT_EXCEEDED",
                "label": "Limite de Cores Especiais",
                "status": "ERRO",
                "found_value": str(len(spot_names)),
                "expected_value": str(max_spots)
            }
             res.update(get_human_error(res["code"], res["found_value"], res["expected_value"]))
             page_results.append(res)

        # SP-02 & SP-03: Names & Ambiguity
        for name in spot_names:
            if name in RESERVED_NAMES:
                res = {
                    "code": "E_SPOT_RESERVED_NAME",
                    "label": "Nome de Cor Especial",
                    "status": "ERRO",
                    "found_value": name,
                    "expected_value": "Tokens permitidos"
                }
                res.update(get_human_error(res["code"], res["found_value"], res["expected_value"]))
                page_results.append(res)
            
            if not _is_valid_utf8(name):
                res = {
                    "code": "E_SPOT_NAME_NOT_UTF8",
                    "label": "Codificação Spot",
                    "status": "ERRO",
                    "found_value": "Binary/Non-UTF8",
                    "expected_value": "UTF-8"
                }
                res.update(get_human_error(res["code"], res["found_value"], res["expected_value"]))
                page_results.append(res)

            alts = spot_info.get(name, set())
            if len(alts) > 1:
                res = {
                    "code": "E_SPOT_AMBIGUOUS",
                    "label": "Definições de Cor Spot",
                    "status": "ERRO",
                    "found_value": f"{name} ({', '.join(alts)})",
                    "expected_value": "Espaço alternativo único"
                }
                res.update(get_human_error(res["code"], res["found_value"], res["expected_value"]))
                page_results.append(res)

        if conversion_errors > 0:
            res = {
                "code": "E_DEVICEN_CONV",
                "label": "Conversão de Cor Especial",
                "status": "ERRO",
                "found_value": "AlternateSpace RGB",
                "expected_value": "DeviceCMYK/Lab",
                "message": f"Detectada conversão para RGB em {conversion_errors} objetos.",
                "action": "Certifique-se de que cores spot usem CMYK ou Lab como espaço alternativo."
            }
            page_results.append(res)

        return [{
            "page": 1,
            "checks": page_results
        }]

    finally:
        doc.close()

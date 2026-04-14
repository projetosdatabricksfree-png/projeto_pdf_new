"""
Optional Content Checker — GWG §4.29 compliance.

Blocks PDFs whose catalog declares OCProperties with a /Configs array, since
alternate visibility configurations let press operators toggle layers and can
hide non-conformant content from validation.
"""
from __future__ import annotations

import re
from typing import Any

import fitz


def _resolve_ocproperties_raw(doc: fitz.Document) -> str | None:
    """Return the raw /OCProperties dict as a PDF string, or None if absent."""
    try:
        catalog_xref = doc.pdf_catalog()
    except Exception:
        return None
    if not catalog_xref:
        return None
    try:
        catalog = doc.xref_object(catalog_xref, compressed=False)
    except Exception:
        return None

    m = re.search(r"/OCProperties\s+(\d+)\s+0\s+R", catalog)
    if m:
        try:
            return doc.xref_object(int(m.group(1)), compressed=False)
        except Exception:
            return None

    m = re.search(r"/OCProperties\s*(<<.*?>>)", catalog, re.DOTALL)
    return m.group(1) if m else None


def _count_configs(ocprops: str) -> int:
    """Count entries inside the /Configs array. Returns 0 when absent."""
    m = re.search(r"/Configs\s*\[(.*?)\]", ocprops, re.DOTALL)
    if not m:
        return 0
    body = m.group(1)
    return len(re.findall(r"\d+\s+0\s+R|<<", body))


def check_oc_configs(file_path: str, profile: dict | None = None) -> dict[str, Any]:
    """GWG §4.29 — OCProperties must not contain /Configs."""
    doc = fitz.open(file_path)
    try:
        ocprops = _resolve_ocproperties_raw(doc)
        if not ocprops:
            return {
                "status": "OK",
                "label": "Optional Content (§4.29)",
                "found_value": "Sem OCProperties",
                "expected_value": "/Configs ausente",
            }

        n = _count_configs(ocprops)
        if n > 0:
            return {
                "status": "ERRO",
                "codigo": "E_OC_CONFIGS_PRESENT",
                "label": "Optional Content (§4.29)",
                "found_value": f"Configs[{n} entries]",
                "expected_value": "absent",
                "descricao": (
                    "Catálogo possui OCProperties.Configs — configurações "
                    "alternativas de visibilidade podem ocultar conteúdo não "
                    "conforme do operador de impressão."
                ),
            }
        return {
            "status": "OK",
            "label": "Optional Content (§4.29)",
            "found_value": "OCProperties.D apenas",
            "expected_value": "/Configs ausente",
        }
    finally:
        doc.close()

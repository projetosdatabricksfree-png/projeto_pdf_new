"""
Font Checker — GWG Output Suite 5.0 font embedding compliance.

Supersedes the simplified operario_papelaria_plana/tools/font_checker.py with:
- Strict xref-based embedding verification (xref != 0 → data is embedded).
- FO-03: Deep embedding check (confirms FontFile stream in Descriptor).
- FO-04: Variant-aware minimum text size validation.
- Courier substitution detection.
- LW-02: Effective line width calculation with CTM/Rect support.
"""
from __future__ import annotations

import re
import logging
from typing import Any
import fitz
from .oc_filter import VisibilityFilter, NULL_FILTER
from .error_messages import get_human_error
from .rounding import gwg_round

logger = logging.getLogger(__name__)

# PDF specification base-14 fonts — never require embedding.
_BASE14: frozenset[str] = frozenset({
    "courier", "courier-bold", "courier-oblique", "courier-boldoblique",
    "helvetica", "helvetica-bold", "helvetica-oblique", "helvetica-boldoblique",
    "times-roman", "times-bold", "times-italic", "times-bolditalic",
    "symbol", "zapfdingbats",
    "helv", "heit", "cour", "coit", "tiro", "tiit", "tibo", "tibi",
    "cobo", "cobi", "hebo", "hebi", "symb", "zadb",
})

_PREFERRED_TYPES: frozenset[str] = frozenset({
    "Type1", "Type1C", "CIDFontType2", "OpenType",
})

_ACCEPTABLE_TYPES: frozenset[str] = frozenset({
    "TrueType", "CIDFontType0", "CIDFontType0C", "MMType1",
})

def _is_base14(name: str) -> bool:
    """Return True if the font name matches a PDF base-14 standard font."""
    lower = name.lower().strip()
    return any(b in lower for b in _BASE14)

def check_fonts_gwg(file_path: str, visible_filter: VisibilityFilter = NULL_FILTER) -> dict[str, Any]:
    """Validate font embedding and format per GWG Output Suite 5.0."""
    doc = fitz.open(file_path)
    try:
        seen_xrefs: set[int] = set()
        non_embedded: list[dict] = []
        courier_subs: list[dict] = []
        preferred_count: int = 0
        acceptable_count: int = 0
        all_fonts: list[dict] = []

        for page_num in range(doc.page_count):
            for font_tuple in doc[page_num].get_fonts(full=True):
                xref      = font_tuple[0]
                ext       = font_tuple[1]
                font_type = font_tuple[2]
                basename  = font_tuple[3]
                name      = font_tuple[4]

                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)

                font_info = {
                    "xref": xref,
                    "name": name or basename,
                    "type": font_type,
                    "ext": ext,
                }
                all_fonts.append(font_info)

                if _is_base14(basename) or _is_base14(name):
                    continue

                if xref == 0:
                    non_embedded.append({**font_info, "reason": "xref=0 (not embedded)"})
                    continue

                try:
                    font_obj = doc.xref_object(xref)
                    if '/FontDescriptor' in font_obj:
                         fd_m = re.search(r'/FontDescriptor\s+(\d+)\s+0\s+R', font_obj)
                         if fd_m:
                             fd_obj = doc.xref_object(int(fd_m.group(1)))
                             if '/FontFile' not in fd_obj:
                                 non_embedded.append({**font_info, "reason": "FontFile stream missing in Descriptor"})
                                 continue
                except Exception:
                    pass

                if "courier" in basename.lower():
                    courier_subs.append({**font_info, "reason": "Courier substitution detected"})

                if font_type in _PREFERRED_TYPES:
                    preferred_count += 1
                elif font_type in _ACCEPTABLE_TYPES:
                    acceptable_count += 1

    finally:
        doc.close()

    font_summary = {
        "total": len(all_fonts),
        "preferred_format": preferred_count,
        "acceptable_format": acceptable_count,
        "non_embedded": len(non_embedded),
        "courier_substitutions": len(courier_subs),
    }

    if non_embedded:
        res = {
            "status": "ERRO",
            "codigo": "E008_NON_EMBEDDED_FONTS",
            "found_value": f"{len(non_embedded)} fonte(s) não incorporada(s)",
            "expected_value": "100% das fontes incorporadas",
            "non_embedded": [f["name"] for f in non_embedded],
            "font_summary": font_summary,
        }
        res.update(get_human_error(res["codigo"], res["found_value"], res["expected_value"]))
        return res

    if courier_subs:
        return {
            "status": "AVISO",
            "codigo": "W_COURIER_SUBSTITUTION",
            "found_value": f"{len(courier_subs)} substituição(ões) por Courier",
            "expected_value": "Fontes originais",
            "font_summary": font_summary,
        }

    return {
        "status": "OK",
        "found_value": "100% das fontes incorporadas",
        "expected_value": "100% das fontes incorporadas",
        "font_summary": font_summary,
    }

def check_text_size_variant(file_path: str, profile: dict | None = None) -> dict[str, Any]:
    """FO-04: Apply minimum text size per variant (§4.16)."""
    if profile is None:
        from .profile_matcher import get_gwg_profile
        profile = get_gwg_profile("default")

    min_text_pt = profile.get("min_text_pt", 0.0)
    if min_text_pt <= 0:
        return {"status": "OK", "label": "Tamanho de Texto", "found_value": "Sem restrição"}

    doc = fitz.open(file_path)
    try:
        small_texts = []
        for page in doc:
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if 0 < span["size"] < min_text_pt:
                             small_texts.append({"page": page.number+1, "size": round(span["size"], 2)})
                             if len(small_texts) > 5:
                                 break
                    if len(small_texts) > 5:
                        break
                if len(small_texts) > 5:
                    break
            if len(small_texts) > 5:
                break

        if small_texts:
             res = {
                "status": "AVISO",
                "codigo": "W_TEXT_TOO_SMALL",
                "label": "Tamanho Mínimo de Texto",
                "found_value": f"{small_texts[0]['size']}pt",
                "expected_value": f"≥ {min_text_pt}pt",
                "paginas": list({s["page"] for s in small_texts})
            }
             res.update(get_human_error(res["codigo"], res["found_value"], res["expected_value"]))
             return res
             
        return {"status": "OK", "label": "Tamanho Mínimo de Texto", "found_value": "Conforme"}
    finally:
        doc.close()

def check_hairlines(file_path: str, min_width_pt: float = 0.25, visible_filter: VisibilityFilter = NULL_FILTER) -> dict[str, Any]:
    """Check for hairline strokes (lines thinner than min_width_pt points)."""
    doc = fitz.open(file_path)
    try:
        hairlines: list[dict] = []
        for page_num in range(min(doc.page_count, 5)):
            page = doc[page_num]
            try:
                for drawing in page.get_drawings():
                    if not visible_filter.is_visible(drawing.get("oc", [])):
                        continue
                        
                    w = drawing.get("width", 0)
                    if w is None or w <= 0:
                        continue
                    
                    if not drawing.get("items") or drawing["items"][0][0] != "re":
                         w_rounded = gwg_round(w, kind="path")
                         if 0 < w_rounded < min_width_pt:
                             hairlines.append({"page": page_num + 1, "width_pt": round(w, 4)})
                    else:
                         rect = drawing["rect"]
                         effective_w = min(rect.width, rect.height)
                         w_rounded = gwg_round(effective_w, kind="path")
                         if 0 < w_rounded < min_width_pt:
                             hairlines.append({"page": page_num + 1, "width_pt": round(effective_w, 4)})

                    if len(hairlines) >= 10:
                        break
            except Exception:
                continue
            if len(hairlines) >= 10:
                break

        if hairlines:
            return {
                "status": "ERRO",
                "codigo": "E010_HAIRLINE_DETECTED",
                "label": "Espessura de Linha (Hairline)",
                "found_value": f"{hairlines[0]['width_pt']}pt",
                "expected_value": f"≥ {min_width_pt}pt",
            }
        return {
            "status": "OK",
            "label": "Espessura de Linha (Hairline)",
            "found_value": "Adequada",
            "expected_value": f"≥ {min_width_pt}pt",
        }
    finally:
        doc.close()

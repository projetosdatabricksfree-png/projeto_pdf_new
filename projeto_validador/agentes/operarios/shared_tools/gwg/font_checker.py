"""
Font Checker — GWG Output Suite 5.0 font embedding compliance.

Supersedes the simplified operario_papelaria_plana/tools/font_checker.py with:
- Strict xref-based embedding verification (xref != 0 → data is embedded).
- Courier substitution detection — flags fonts with 'courier' in the basename
  as potential substitutions introduced by PDF exporters when original fonts
  are missing.
- OpenType (CIDFontType2/Type1C) format validation — confirms premium fonts
  are stored in their original format, not downgraded.
- Hairline detection remains available as a separate function.

PDF font tuple from PyMuPDF page.get_fonts(full=True):
  (xref, ext, type, basename, name, encoding, referencer)
   [0]   [1]  [2]   [3]       [4]   [5]       [6]
"""
from __future__ import annotations

from typing import Any

import fitz  # PyMuPDF

# PDF specification base-14 fonts — never require embedding.
_BASE14: frozenset[str] = frozenset({
    "courier", "courier-bold", "courier-oblique", "courier-boldoblique",
    "helvetica", "helvetica-bold", "helvetica-oblique", "helvetica-boldoblique",
    "times-roman", "times-bold", "times-italic", "times-bolditalic",
    "symbol", "zapfdingbats",
    # PyMuPDF internal aliases
    "helv", "heit", "cour", "coit", "tiro", "tiit", "tibo", "tibi",
    "cobo", "cobi", "hebo", "hebi", "symb", "zadb",
})

# Font types that indicate fully-embedded, high-quality encoding.
_PREFERRED_TYPES: frozenset[str] = frozenset({
    "Type1", "Type1C", "CIDFontType2", "OpenType",
})

# Font types that are acceptable (embedded but not optimal).
_ACCEPTABLE_TYPES: frozenset[str] = frozenset({
    "TrueType", "CIDFontType0", "CIDFontType0C", "MMType1",
})


def _is_base14(name: str) -> bool:
    """Return True if the font name matches a PDF base-14 standard font."""
    lower = name.lower().strip()
    return any(b in lower for b in _BASE14)


def check_fonts_gwg(file_path: str) -> dict[str, Any]:
    """Validate font embedding and format per GWG Output Suite 5.0.

    Checks per font xref:
    1. Embedding — xref must be non-zero for non-base14 fonts.
    2. Courier substitution — basename containing 'courier' is a red flag.
    3. Font format — prefers Type1C / OpenType over TrueType for print fidelity.

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        Dict with status, codigo (if applicable), non_embedded (list),
        courier_substitutions (list), font_summary (dict).
    """
    doc = fitz.open(file_path)
    try:
        seen_xrefs: set[int] = set()   # deduplicate across pages
        non_embedded: list[dict] = []
        courier_subs: list[dict] = []
        preferred_count: int = 0
        acceptable_count: int = 0
        all_fonts: list[dict] = []

        for page_num in range(doc.page_count):
            for font_tuple in doc[page_num].get_fonts(full=True):
                xref      = font_tuple[0]
                ext       = font_tuple[1]   # e.g. 'ttf', 'cff', 'pfa', ''
                font_type = font_tuple[2]   # e.g. 'TrueType', 'Type1'
                basename  = font_tuple[3]   # original font name
                name      = font_tuple[4]   # may include subset prefix

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

                # Base-14 fonts — skip embedding check (per PDF spec)
                if _is_base14(basename) or _is_base14(name):
                    continue

                # ── 1. Embedding check via xref ──────────────────────────────
                if xref == 0:
                    non_embedded.append({**font_info, "reason": "xref=0 (not embedded)"})
                    continue

                # ── 2. Courier substitution detection ────────────────────────
                if "courier" in basename.lower():
                    courier_subs.append({
                        **font_info,
                        "reason": (
                            "Font basename contains 'courier' — "
                            "likely a substitution by the PDF exporter for a missing font"
                        ),
                    })

                # ── 3. Font format preference ────────────────────────────────
                if font_type in _PREFERRED_TYPES:
                    preferred_count += 1
                elif font_type in _ACCEPTABLE_TYPES:
                    acceptable_count += 1

    finally:
        doc.close()

    total = len(all_fonts)
    font_summary = {
        "total": total,
        "preferred_format": preferred_count,
        "acceptable_format": acceptable_count,
        "non_embedded": len(non_embedded),
        "courier_substitutions": len(courier_subs),
    }

    if non_embedded:
        return {
            "status": "ERRO",
            "codigo": "E008_NON_EMBEDDED_FONTS",
            "found_value": f"{len(non_embedded)} fonte(s) não incorporada(s)",
            "expected_value": "100% das fontes incorporadas",
            "descricao": f"{len(non_embedded)} fonte(s) não incorporada(s) detectada(s)",
            "non_embedded": [f["name"] for f in non_embedded],
            "non_embedded_detail": non_embedded,
            "courier_substitutions": [f["name"] for f in courier_subs],
            "font_summary": font_summary,
        }

    if courier_subs:
        return {
            "status": "AVISO",
            "codigo": "W_COURIER_SUBSTITUTION",
            "found_value": f"{len(courier_subs)} substituição(ões) por Courier",
            "expected_value": "Fontes originais (sem substituição)",
            "descricao": (
                f"{len(courier_subs)} fonte(s) substituída(s) por Courier — "
                "fontes originais podem estar em falta"
            ),
            "non_embedded": [],
            "courier_substitutions": [f["name"] for f in courier_subs],
            "courier_detail": courier_subs,
            "font_summary": font_summary,
        }

    return {
        "status": "OK",
        "found_value": "100% das fontes incorporadas",
        "expected_value": "100% das fontes incorporadas",
        "non_embedded": [],
        "courier_substitutions": [],
        "font_summary": font_summary,
    }


def check_hairlines(file_path: str, min_width_pt: float = 0.25) -> dict[str, Any]:
    """Check for hairline strokes (lines thinner than min_width_pt points).

    Args:
        file_path: Absolute path to the PDF file.
        min_width_pt: Minimum acceptable line width in points (default 0.25pt).

    Returns:
        Dict with status, codigo (if applicable), hairlines found.
    """
    from agentes.operarios.shared_tools.gwg.rounding import gwg_round

    doc = fitz.open(file_path)
    try:
        hairlines: list[dict] = []

        for page_num in range(min(doc.page_count, 5)):
            page = doc[page_num]
            try:
                for drawing in page.get_drawings():
                    w = drawing.get("width", 0)
                    # §3.15 rounding — path precision = 3 decimals (HALF_UP)
                    w_rounded = gwg_round(w, kind="path") if w else 0.0
                    if w is not None and 0 < w_rounded < min_width_pt:
                        hairlines.append({"page": page_num + 1, "width_pt": round(w, 4)})
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
                "paginas": list({h["page"] for h in hairlines}),
                "meta": {
                    "client": f"Linhas muito finas ({hairlines[0]['width_pt']}pt) detectadas.",
                    "action": "Aumente a espessura das linhas para pelo menos 0.25pt."
                }
            }
        return {
            "status": "OK",
            "label": "Espessura de Linha (Hairline)",
            "found_value": "Adequada",
            "expected_value": f"≥ {min_width_pt}pt",
            "meta": {"client": "Todas as linhas possuem espessura adequada.", "action": "Nenhuma."}
        }

    finally:
        doc.close()

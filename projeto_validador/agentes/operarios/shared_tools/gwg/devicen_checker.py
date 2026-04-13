"""
DeviceN / Separation Checker — GWG Output Suite 5.0 spot colour compliance.

Inspects every xref for /Separation and /DeviceN colour space arrays and:
- Extracts spot colour names (Pantone, HKS, custom inks).
- Detects accidental conversion of DeviceN to its AlternateSpace (CMYK/RGB),
  which loses spot colour fidelity and triggers a GWG blocking error.
- Alerts when a /Separation space uses a non-CMYK alternate (e.g. RGB fallback).

PDF syntax reference:
  /Separation name alternateSpace tintTransform
  /DeviceN [name ...] alternateSpace tintTransform attributes
"""
from __future__ import annotations

import re
from typing import Any

import fitz  # PyMuPDF

# Spot colours that are expected to remain as-is (not converted to alternate)
_PANTONE_PATTERN = re.compile(r"(?i)(pantone|pms|hks|cmyk|spot|special)", re.IGNORECASE)

# Alternate spaces that indicate RGB fallback (problematic for print)
_RGB_ALTERNATES: frozenset[str] = frozenset({"DeviceRGB", "CalRGB"})
_CMYK_ALTERNATES: frozenset[str] = frozenset({"DeviceCMYK", "DeviceGray"})


def _parse_separation_space(obj_str: str) -> dict[str, Any] | None:
    """Parse a /Separation colour space array from an xref object string.

    Returns a dict with keys: name, alternate, or None if not a Separation space.
    """
    # Separation arrays look like: [/Separation /PantoneCoolGray /DeviceCMYK ...]
    m = re.search(
        r"\[\s*/Separation\s+/([^\s/\]]+)\s+/(\w+)",
        obj_str,
    )
    if not m:
        # Sometimes stored as name object: /Separation /Name /Alt ...
        m = re.search(r"/Separation\s+/([^\s/]+)\s+/(\w+)", obj_str)
    if not m:
        return None
    return {"name": m.group(1), "alternate": m.group(2), "type": "Separation"}


def _parse_devicen_space(obj_str: str) -> dict[str, Any] | None:
    """Parse a /DeviceN colour space array from an xref object string.

    Returns a dict with keys: names (list), alternate, or None if not DeviceN.
    """
    m = re.search(
        r"\[\s*/DeviceN\s+\[([^\]]+)\]\s+/(\w+)",
        obj_str,
    )
    if not m:
        return None
    # Extract spot colour names from the names array
    raw_names = re.findall(r"/([^\s/\]]+)", m.group(1))
    return {
        "names": [n for n in raw_names if n != "None"],
        "alternate": m.group(2),
        "type": "DeviceN",
    }


def _is_accidental_conversion(space: dict[str, Any]) -> bool:
    """Return True if this colour space signals an accidental alternate-space conversion.

    Conditions:
    - DeviceN whose alternate is RGB (hard error — spot colours lost).
    - DeviceN whose alternate is CMYK but all named inks are standard process
      colours (C/M/Y/K/Black/Cyan/Magenta/Yellow) — may be a false positive,
      so we only flag explicit RGB alternates as ERRORS, CMYK as WARNINGS.
    """
    alternate = space.get("alternate", "")
    return alternate in _RGB_ALTERNATES


def check_devicen(file_path: str) -> dict[str, Any]:
    """Detect /Separation and /DeviceN colour spaces and validate spot colour integrity.

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        Dict with status, codigo, spot_colours (list of names), conversion_issues.
    """
    doc = fitz.open(file_path)
    try:
        spot_colours: list[str] = []
        conversion_issues: list[dict] = []
        spaces_found: list[dict] = []

        for xref in range(1, doc.xref_length()):
            try:
                obj_str = doc.xref_object(xref, compressed=False)
            except Exception:
                continue

            if "/Separation" not in obj_str and "/DeviceN" not in obj_str:
                continue

            # Try Separation first
            sep = _parse_separation_space(obj_str)
            if sep:
                spaces_found.append({**sep, "xref": xref})
                spot_colours.append(sep["name"])
                if sep["alternate"] in _RGB_ALTERNATES:
                    conversion_issues.append({
                        "xref": xref,
                        "type": "Separation",
                        "name": sep["name"],
                        "alternate": sep["alternate"],
                        "severity": "ERRO",
                        "codigo": "E_DEVICEN_CONV",
                    })
                continue

            # Try DeviceN
            dn = _parse_devicen_space(obj_str)
            if dn:
                spaces_found.append({**dn, "xref": xref})
                spot_colours.extend(dn["names"])
                if _is_accidental_conversion(dn):
                    conversion_issues.append({
                        "xref": xref,
                        "type": "DeviceN",
                        "names": dn["names"],
                        "alternate": dn["alternate"],
                        "severity": "ERRO",
                        "codigo": "E_DEVICEN_CONV",
                    })
                elif dn["alternate"] in _CMYK_ALTERNATES and not dn["names"]:
                    # DeviceN with only process colours and CMYK alternate — suspicious
                    conversion_issues.append({
                        "xref": xref,
                        "type": "DeviceN",
                        "names": dn["names"],
                        "alternate": dn["alternate"],
                        "severity": "AVISO",
                        "codigo": "W_DEVICEN_CMYK_ALT",
                    })

    finally:
        doc.close()

    unique_spots = sorted(set(spot_colours))
    has_errors = any(i["severity"] == "ERRO" for i in conversion_issues)
    
    found_str = f"{len(unique_spots)} cores spot: {', '.join(unique_spots[:3])}" + ("..." if len(unique_spots)>3 else "") if unique_spots else "Nenhuma cor spot"
    expected_str = "AlternateSpace != RGB"

    if has_errors:
        return {
            "status": "ERRO",
            "codigo": "E_DEVICEN_CONV",
            "found_value": "AlternateSpace RGB Detectado",
            "expected_value": expected_str,
            "descricao": (
                f"Conversão acidental de DeviceN/Separation para AlternateSpace RGB detectada "
                f"em {sum(1 for i in conversion_issues if i['severity'] == 'ERRO')} espaço(s)"
            ),
            "spot_colours": unique_spots,
            "conversion_issues": conversion_issues,
            "spaces_found": len(spaces_found),
        }

    if conversion_issues:
        return {
            "status": "AVISO",
            "codigo": "W_DEVICEN_CMYK_ALT",
            "found_value": "AlternateSpace CMYK",
            "expected_value": expected_str,
            "descricao": "DeviceN com AlternateSpace CMYK detectado — verificar fidelidade das cores spot",
            "spot_colours": unique_spots,
            "conversion_issues": conversion_issues,
            "spaces_found": len(spaces_found),
        }

    return {
        "status": "OK",
        "found_value": found_str,
        "expected_value": expected_str,
        "spot_colours": unique_spots,
        "spaces_found": len(spaces_found),
        "conversion_issues": [],
    }

"""
ICC Profile Checker — GWG Output Suite 5.0 / PDF/X-4 output intent compliance.

Inspects:
- OutputIntents in the PDF catalog (mandatory for PDF/X-4).
- /ICCBased colour spaces embedded in the document.
- ICC profile version extracted from the binary stream header:
    bytes[0]  = major version (e.g. 2 or 4)
    bytes[1]  = minor/patch (encoded as BCD)
  GWG permits ICC v2 and v4; warns on v4 because legacy RIPs may reject it.

Anti-OOM (Rule 1): ICC streams are read in header-only mode — only the first
128 bytes (ICC profile header size) are consumed, never the full stream.
"""
from __future__ import annotations

import re
import struct
from typing import Any

import fitz  # PyMuPDF

# ICC profile header: first 128 bytes.  The version field is at offset 8.
_ICC_HEADER_SIZE: int = 128
_ICC_VERSION_OFFSET: int = 8   # 4-byte big-endian version field


def _read_icc_version(stream_bytes: bytes) -> tuple[int, int] | None:
    """Extract (major, minor) from an ICC profile binary stream.

    The 4-byte version field at offset 8 encodes:
      byte 0 = major (e.g. 0x02 for v2, 0x04 for v4)
      byte 1 = minor/patch (BCD-encoded, e.g. 0x40 = 4.0)
      bytes 2-3 = reserved, should be 0x0000

    Returns None if the stream is too short or does not look like an ICC profile.
    """
    if len(stream_bytes) < _ICC_HEADER_SIZE:
        return None
    major = stream_bytes[_ICC_VERSION_OFFSET]
    minor_bcd = stream_bytes[_ICC_VERSION_OFFSET + 1]
    minor = (minor_bcd >> 4) * 10 + (minor_bcd & 0x0F)
    if major not in (2, 4):  # sanity check
        return None
    return (major, minor)


def _find_output_intents(doc: fitz.Document) -> list[dict[str, Any]]:
    """Return OutputIntent entries from the PDF catalog."""
    intents: list[dict[str, Any]] = []

    cat_xref = doc.pdf_catalog()
    if cat_xref <= 0:
        return intents

    cat_obj = doc.xref_object(cat_xref, compressed=False)
    if "/OutputIntents" not in cat_obj:
        return intents

    # Find xref of the OutputIntents array
    m = re.search(r"/OutputIntents\s+(\d+)\s+\d+\s+R", cat_obj)
    if not m:
        # Might be an inline array — mark as present but unresolved
        return [{"type": "inline", "icc_version": None}]

    oi_xref = int(m.group(1))
    try:
        oi_obj = doc.xref_object(oi_xref, compressed=False)
    except Exception:
        return intents

    # Find each OutputIntent dict reference
    for intent_xref_str in re.findall(r"(\d+)\s+\d+\s+R", oi_obj):
        intent_xref = int(intent_xref_str)
        try:
            intent_obj = doc.xref_object(intent_xref, compressed=False)
        except Exception:
            continue

        intent: dict[str, Any] = {"xref": intent_xref, "icc_version": None}

        # Extract the DestOutputProfile xref (the ICC stream)
        m_profile = re.search(r"/DestOutputProfile\s+(\d+)\s+\d+\s+R", intent_obj)
        if m_profile:
            profile_xref = int(m_profile.group(1))
            try:
                if doc.xref_is_stream(profile_xref):
                    # Anti-OOM: read only the header bytes
                    raw = doc.xref_stream(profile_xref)
                    if raw:
                        version = _read_icc_version(raw[:_ICC_HEADER_SIZE])
                        intent["icc_version"] = version
            except Exception:
                pass

        # Extract OutputConditionIdentifier (e.g. "FOGRA39")
        m_id = re.search(r"/OutputConditionIdentifier\s*\(([^)]+)\)", intent_obj)
        if m_id:
            intent["output_condition"] = m_id.group(1).strip()

        intents.append(intent)

    return intents


def _find_iccbased_spaces(doc: fitz.Document) -> list[dict[str, Any]]:
    """Scan all xrefs for /ICCBased colour space streams."""
    spaces: list[dict[str, Any]] = []

    for xref in range(1, doc.xref_length()):
        try:
            obj_str = doc.xref_object(xref, compressed=False)
        except Exception:
            continue

        # ICCBased colour space arrays refer to a stream xref
        if "/ICCBased" not in obj_str and "/N " not in obj_str:
            continue

        if not doc.xref_is_stream(xref):
            continue

        # Check number of colour components (/N key)
        m_n = re.search(r"/N\s+(\d+)", obj_str)
        n_components = int(m_n.group(1)) if m_n else None

        space: dict[str, Any] = {
            "xref": xref,
            "n_components": n_components,
            "icc_version": None,
        }

        try:
            raw = doc.xref_stream(xref)
            if raw:
                version = _read_icc_version(raw[:_ICC_HEADER_SIZE])
                space["icc_version"] = version
        except Exception:
            pass

        spaces.append(space)

    return spaces


def check_icc(file_path: str) -> dict[str, Any]:
    """Validate ICC profile and OutputIntent compliance for GWG/PDF/X-4.

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        Dict with status, codigo (if applicable), output_intents, icc_spaces,
        has_output_intent (bool), icc_v4_detected (bool).
    """
    doc = fitz.open(file_path)
    try:
        output_intents = _find_output_intents(doc)
        icc_spaces = _find_iccbased_spaces(doc)
    finally:
        doc.close()

    has_output_intent = len(output_intents) > 0

    # Check for ICC v4 (warns — legacy RIP risk)
    icc_v4_detected = any(
        space.get("icc_version") and space["icc_version"][0] == 4
        for space in icc_spaces
    ) or any(
        intent.get("icc_version") and intent["icc_version"][0] == 4
        for intent in output_intents
    )

    if not has_output_intent:
        return {
            "status": "AVISO",
            "codigo": "W_NO_OUTPUT_INTENT",
            "descricao": "Nenhum OutputIntent encontrado — PDF/X-4 exige OutputIntent para conformidade GWG",
            "output_intents": [],
            "icc_spaces": len(icc_spaces),
            "has_output_intent": False,
            "icc_v4_detected": icc_v4_detected,
        }

    if icc_v4_detected:
        return {
            "status": "AVISO",
            "codigo": "W_ICC_V4",
            "descricao": "Perfil ICC versão 4 detectado — RIPs antigos podem rejeitar este perfil",
            "output_intents": output_intents,
            "icc_spaces": len(icc_spaces),
            "has_output_intent": True,
            "icc_v4_detected": True,
        }

    return {
        "status": "OK",
        "output_intents": output_intents,
        "icc_spaces": len(icc_spaces),
        "has_output_intent": True,
        "icc_v4_detected": False,
    }

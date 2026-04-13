"""
OPM Checker — GWG Output Suite 5.0 / PDF/X-4 Overprint Mode compliance.

Two-layer inspection:
1. PyMuPDF — reads ExtGState dictionary entries (OPM, OP, op) from all xrefs.
2. Ghostscript subprocess (Rule 2 — Subprocesso Seguro) — hooks setoverprint and
   setcmykcolor at the PostScript interpreter level to detect White Overprint and
   Gray Overprint at render time, where the color state is definitively known.

GWG requirement: OPM must be 1 (not 0) for any object that has overprint active.
White Overprint (CMYK 0,0,0,0 + OP=true) is a blocking error; it causes objects
to vanish at the RIP.  Gray Overprint (K-only + OP=true with OPM=0) is a warning.
"""
from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

GS_TIMEOUT: int = 30  # seconds

# PostScript hook injected before the PDF is processed by GS (Rule 2).
# Intercepts setoverprint and setcmykcolor to detect problematic combinations.
_GS_OPM_HOOK: str = (
    # Track overprint state across graphics state changes
    "/gwg_op false def "
    "/real_setoverprint /setoverprint load def "
    "/setoverprint { "
    "  dup /gwg_op exch def "
    "  real_setoverprint "
    "} bind def "
    # Intercept CMYK color setting and cross-check with overprint state
    "/real_scmyk /setcmykcolor load def "
    "/setcmykcolor { "
    # White overprint: all components zero, overprint ON → vanishing object
    "  4 copy add add add 0 eq gwg_op and { "
    "    (GWG_WHITE_OVERPRINT) = flush "
    "  } if "
    # Gray overprint: C+M+Y=0, K>0, overprint ON (risky with OPM 0)
    "  4 copy pop add add 0 eq "   # C+M+Y == 0
    "  3 1 roll 0 gt and "          # K > 0
    "  gwg_op and { "
    "    (GWG_GRAY_OVERPRINT) = flush "
    "  } if "
    "  real_scmyk "
    "} bind def "
)


def _sanitize_path(file_path: str) -> str:
    """Reject paths with shell-injection characters and resolve to absolute path."""
    if re.search(r'[;&|`$(){}]', file_path):
        raise ValueError(f"Suspicious characters in file path: {file_path}")
    resolved = str(Path(file_path).resolve())
    if not Path(resolved).exists():
        raise FileNotFoundError(f"File not found: {resolved}")
    return resolved


def _parse_xref_num(ref_str: str) -> int | None:
    """Extract the object number from an indirect reference string ('5 0 R' → 5)."""
    m = re.match(r"^'?(\d+)", ref_str.strip())
    return int(m.group(1)) if m else None


def _extract_extgstate_entries(doc: fitz.Document) -> list[dict[str, Any]]:
    """Return a list of parsed ExtGState dictionaries found in the document.

    Iterates all xrefs and collects objects that appear to be ExtGState dicts
    by looking for the characteristic keys (OPM, OP, op, BM, SMask).
    """
    entries: list[dict[str, Any]] = []

    for xref in range(1, doc.xref_length()):
        try:
            obj_str = doc.xref_object(xref, compressed=False)
        except Exception:
            continue

        # ExtGState objects contain at least one of these keys
        if not any(k in obj_str for k in ("/OPM", "/OP ", "/op ", "/BM")):
            continue

        entry: dict[str, Any] = {"xref": xref, "raw": obj_str}

        # Parse OPM value (0 or 1)
        m_opm = re.search(r"/OPM\s+(\d+)", obj_str)
        if m_opm:
            entry["OPM"] = int(m_opm.group(1))

        # Parse OP (overprint for painting operators)
        m_op = re.search(r"/OP\s+(true|false)", obj_str)
        if m_op:
            entry["OP"] = m_op.group(1) == "true"

        # Parse op (overprint for non-painting operators)
        m_op_lower = re.search(r"/op\s+(true|false)", obj_str)
        if m_op_lower:
            entry["op"] = m_op_lower.group(1) == "true"

        entries.append(entry)

    return entries


def _gs_detect_overprint_issues(file_path: str) -> dict[str, Any]:
    """Run GS subprocess with PostScript hooks to detect overprint colour issues.

    Rule 2 — Subprocesso Seguro: subprocess.run with shell=False, explicit timeout,
    return-code checked.  Output parsed from stdout.

    Returns:
        Dict with keys: white_overprint (bool), gray_overprint (bool), gs_ok (bool).
    """
    safe_path = _sanitize_path(file_path)

    cmd = [
        "gs",
        "-dBATCH",
        "-dNOPAUSE",
        "-sDEVICE=nullpage",
        "-q",           # suppress banner
        "-c", _GS_OPM_HOOK,
        "-f", safe_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            timeout=GS_TIMEOUT,
            capture_output=True,
            text=True,
            shell=False,  # Rule 2 — never shell=True
        )
    except subprocess.TimeoutExpired:
        logger.warning("[opm_checker] GS timed out after %ds — skipping GS pass", GS_TIMEOUT)
        return {"white_overprint": False, "gray_overprint": False, "gs_ok": False}
    except FileNotFoundError:
        logger.warning("[opm_checker] GS binary not found — skipping GS pass")
        return {"white_overprint": False, "gray_overprint": False, "gs_ok": False}

    if result.returncode not in (0, 1):  # GS may return 1 for warnings
        logger.warning("[opm_checker] GS exited with code %d", result.returncode)

    output = result.stdout + result.stderr
    return {
        "white_overprint": "GWG_WHITE_OVERPRINT" in output,
        "gray_overprint": "GWG_GRAY_OVERPRINT" in output,
        "gs_ok": True,
    }


def check_opm(file_path: str) -> dict[str, Any]:
    """Validate OPM (Overprint Mode) compliance per GWG Output Suite 5.0.

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        Dict compatible with operário validation_results format:
          status: "OK" | "ERRO" | "AVISO"
          codigo: GWG error/warning code (if applicable)
          opm_entries: list of detected ExtGState OPM entries
          white_overprint: bool
          gray_overprint: bool
    """
    doc = fitz.open(file_path)
    try:
        ext_gstate_entries = _extract_extgstate_entries(doc)
    finally:
        doc.close()

    # --- PyMuPDF pass: structural OPM analysis ---
    opm_violations: list[dict] = []
    for entry in ext_gstate_entries:
        opm_val = entry.get("OPM")
        op_active = entry.get("OP", False) or entry.get("op", False)

        if op_active and opm_val == 0:
            opm_violations.append({
                "xref": entry["xref"],
                "OPM": 0,
                "OP": op_active,
                "issue": "OPM=0 with overprint active — colour accuracy compromised",
            })

    # --- Ghostscript pass: render-time white/gray overprint detection (Rule 2) ---
    gs_result = _gs_detect_overprint_issues(file_path)

    # --- Determine verdict ---
    if gs_result["white_overprint"]:
        return {
            "status": "ERRO",
            "codigo": "E_WHITE_OVERPRINT",
            "descricao": "White Overprint detectado (CMYK 0,0,0,0 com overprint ativo)",
            "opm_entries": opm_violations,
            "white_overprint": True,
            "gray_overprint": gs_result["gray_overprint"],
            "gs_validated": gs_result["gs_ok"],
        }

    if opm_violations:
        return {
            "status": "ERRO",
            "codigo": "E_OPM_WRONG",
            "descricao": f"OPM=0 encontrado em {len(opm_violations)} entrada(s) ExtGState com overprint ativo",
            "opm_entries": opm_violations,
            "white_overprint": False,
            "gray_overprint": gs_result["gray_overprint"],
            "gs_validated": gs_result["gs_ok"],
        }

    if gs_result["gray_overprint"]:
        return {
            "status": "AVISO",
            "codigo": "W_GRAY_OVERPRINT",
            "descricao": "Gray Overprint detectado (K-only com overprint ativo) — verificar OPM",
            "opm_entries": opm_violations,
            "white_overprint": False,
            "gray_overprint": True,
            "gs_validated": gs_result["gs_ok"],
        }

    return {
        "status": "OK",
        "opm_entries": [e for e in ext_gstate_entries if "OPM" in e],
        "white_overprint": False,
        "gray_overprint": False,
        "gs_validated": gs_result["gs_ok"],
    }

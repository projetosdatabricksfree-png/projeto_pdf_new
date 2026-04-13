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
    # Robust check using Ghostscript's internal color conversion
    "/gwg_check { "
    "  currentoverprint { "
    "    currentcmykcolor "
    "    4 copy add add add 0 eq { (GWG_WHITE_OVERPRINT) = flush } if "
    "    pop pop pop 0 gt { (GWG_GRAY_OVERPRINT) = flush } if " # Simplified Gray check
    "  } if "
    "} bind def "
    # Redefine painting operators to include our check
    "/fill { gwg_check fill } bind def "
    "/stroke { gwg_check stroke } bind def "
    "/show { gwg_check show } bind def "
    "/ashow { gwg_check ashow } bind def "
    "/widthshow { gwg_check widthshow } bind def "
    "/awidthshow { gwg_check awidthshow } bind def "
    "/kshow { gwg_check kshow } bind def "
    "/xshow { gwg_check xshow } bind def "
    "/yshow { gwg_check yshow } bind def "
    "/xyshow { gwg_check xyshow } bind def "
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


def _python_detect_white_overprint(doc: fitz.Document) -> bool:
    """Fallback structural scan for White Overprint.
    
    Finds ExtGState xrefs with OP true and checks if they are used near white color settings.
    """
    op_xrefs = set()
    for xref in range(1, doc.xref_length()):
        try:
            obj = doc.xref_object(xref)
            if '/OP true' in obj or '/op true' in obj:
                op_xrefs.add(xref)
        except: continue
        
    if not op_xrefs:
        return False

    for page in doc:
        # Search page resources for GS names mapping to our OP xrefs
        page_dict = doc.xref_object(page.xref)
        gs_map = {}
        # Simple regex to find /GSName 123 0 R inside /ExtGState << ... >>
        gs_section = re.search(r'/ExtGState\s*<<([^>]*)>>', page_dict)
        if gs_section:
            for gs_name, ref_xref in re.findall(r'/(\w+)\s+(\d+)\s+0\s+R', gs_section.group(1)):
                if int(ref_xref) in op_xrefs:
                    gs_map[gs_name] = int(ref_xref)
        
        if gs_map:
            content = b"".join([doc.xref_stream(c) for c in page.get_contents()]).decode("latin-1", errors="ignore")
            for gs_name in gs_map:
                # Look for '/GSName gs' pattern
                gs_call = f"/{gs_name} gs"
                if gs_call in content:
                    # Look for nearby white color settings: '0 0 0 0 k', '0 0 0 0 K', '1 g', '1 G'
                    # We check 500 chars around the gs call as a heuristic
                    pos = content.find(gs_call)
                    context = content[max(0, pos-200):min(len(content), pos+200)]
                    if any(x in context for x in ["0 0 0 0 k", "0 0 0 0 K", "1 g", "1 G"]):
                        logger.info(f"[opm_checker] Structural White Overprint found on page {page.number}")
                        return True
    return False


def check_opm(file_path: str) -> dict[str, Any]:
    """Validate OPM (Overprint Mode) compliance per GWG Output Suite 5.0."""
    doc = fitz.open(file_path)
    try:
        ext_gstate_entries = _extract_extgstate_entries(doc)
        
        # --- Python pass: structural White Overprint analysis ---
        python_white_op = _python_detect_white_overprint(doc)
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

    # --- Ghostscript pass: render-time white/gray overprint detection ---
    gs_result = _gs_detect_overprint_issues(file_path)
    
    white_overprint = gs_result["white_overprint"] or python_white_op

    # --- Determine verdict ---
    if white_overprint:
        return {
            "status": "ERRO",
            "codigo": "E_WHITE_OVERPRINT",
            "found_value": "White Overprint Detectado",
            "expected_value": "C0 M0 Y0 K0 + Overprint=False",
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
            "found_value": "OPM=0 (Incorreto)",
            "expected_value": "OPM=1 (PDF/X-4 Standard)",
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
            "found_value": "K-only + Overprint Active",
            "expected_value": "OPM=1 (K-overprint Safe)",
            "descricao": "Gray Overprint detectado (K-only com overprint ativo) — verificar OPM",
            "opm_entries": opm_violations,
            "white_overprint": False,
            "gray_overprint": True,
            "gs_validated": gs_result["gs_ok"],
        }

    return {
        "status": "OK",
        "found_value": "OPM=1 ou Overprint Inativo",
        "expected_value": "OPM=1 para Overprint Ativo",
        "opm_entries": [e for e in ext_gstate_entries if "OPM" in e],
        "white_overprint": False,
        "gray_overprint": False,
        "gs_validated": gs_result["gs_ok"],
    }

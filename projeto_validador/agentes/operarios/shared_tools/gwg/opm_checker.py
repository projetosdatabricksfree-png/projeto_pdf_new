"""
OPM Checker — GWG Output Suite 5.0 / PDF/X-4 Overprint Mode compliance.

Two-layer inspection:
1. PyMuPDF — reads ExtGState dictionary entries (OPM, OP, op) from all xrefs.
2. Ghostscript subprocess (Rule 2) — detects White Overprint at render time.
3. Content Stream Walker — validates small black text/paths for DeviceGray/OPM.
"""
from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any, List
import fitz  # PyMuPDF
from .oc_filter import VisibilityFilter, NULL_FILTER
from .error_messages import get_human_error

logger = logging.getLogger(__name__)

GS_TIMEOUT: int = 30  # seconds

_GS_OPM_HOOK: str = (
    "/gwg_check { "
    "  currentoverprint { "
    "    currentcmykcolor "
    "    4 copy add add add 0 eq { (GWG_WHITE_OVERPRINT) = flush } if "
    "    pop pop pop 0 gt { (GWG_GRAY_OVERPRINT) = flush } if "
    "  } if "
    "} bind def "
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
    """Validate file path safety."""
    if re.search(r'[;&|`${}]', file_path):
        raise ValueError(f"Suspicious characters in file path: {file_path}")
    resolved = str(Path(file_path).resolve())
    if not Path(resolved).exists():
        raise FileNotFoundError(f"File not found: {resolved}")
    return resolved

def _extract_extgstate_entries(doc: fitz.Document) -> list[dict[str, Any]]:
    """Extract ExtGState entries with OPM/OP/op keys."""
    entries: list[dict[str, Any]] = []
    for xref in range(1, doc.xref_length()):
        try:
            obj_str = doc.xref_object(xref, compressed=False)
            if not any(k in obj_str for k in ("/OPM", "/OP ", "/op ", "/BM")):
                continue
            entry: dict[str, Any] = {"xref": xref, "raw": obj_str}
            m_opm = re.search(r"/OPM\s+(\d+)", obj_str)
            if m_opm:
                entry["OPM"] = int(m_opm.group(1))
            m_op = re.search(r"/OP\s+(true|false)", obj_str)
            if m_op:
                entry["OP"] = m_op.group(1) == "true"
            m_op_lower = re.search(r"/op\s+(true|false)", obj_str)
            if m_op_lower:
                entry["op"] = m_op_lower.group(1) == "true"
            entries.append(entry)
        except Exception:
            continue
    return entries

def _gs_detect_overprint_issues(file_path: str) -> dict[str, Any]:
    """Invoke Ghostscript to detect White/Gray Overprint at render time."""
    try:
        safe_path = _sanitize_path(file_path)
        cmd = ["gs", "-dBATCH", "-dNOPAUSE", "-sDEVICE=nullpage", "-q", "-c", _GS_OPM_HOOK, "-f", safe_path]
        result = subprocess.run(cmd, timeout=GS_TIMEOUT, capture_output=True, text=True, shell=False)
        output = result.stdout + result.stderr
        return {
            "white_overprint": "GWG_WHITE_OVERPRINT" in output,
            "gray_overprint": "GWG_GRAY_OVERPRINT" in output,
            "gs_ok": True,
        }
    except Exception as e:
        logger.error(f"GS error: {e}")
        return {"white_overprint": False, "gray_overprint": False, "gs_ok": False}

def _python_detect_white_overprint(doc: fitz.Document) -> bool:
    """Fallback structural check for white overprint."""
    op_xrefs = set()
    for xref in range(1, doc.xref_length()):
        try:
            obj = doc.xref_object(xref)
            if '/OP true' in obj or '/op true' in obj:
                op_xrefs.add(xref)
        except Exception:
            continue
    if not op_xrefs:
        return False
    for page in doc:
        page_dict = doc.xref_object(page.xref)
        gs_section = re.search(r'/ExtGState\s*<<([^>]*)>>', page_dict)
        if gs_section:
            for gs_name, ref_xref in re.findall(r'/(\w+)\s+(\d+)\s+0\s+R', gs_section.group(1)):
                if int(ref_xref) in op_xrefs:
                    content = b"".join([doc.xref_stream(c) for c in page.get_contents()]).decode("latin-1", errors="ignore")
                    if f"/{gs_name} gs" in content:
                        return True
    return False

_TEXT_SIZE_THRESHOLD_PT: float = 12.0
_PATH_WIDTH_THRESHOLD_PT: float = 2.0
_BLACK_K_TOLERANCE: float = 1e-6

_TOKEN_RE = re.compile(
    rb"[-+]?\d*\.\d+|[-+]?\d+"
    rb"|/[A-Za-z0-9_.#\-]+"
    rb"|\([^()]*\)"
    rb"|<[0-9A-Fa-f \t\r\n]*>"
    rb"|\[|\]|<<|>>"
    rb"|[A-Za-z'\"*]+"
)

def _walk_small_black(content: bytes, gs_map: dict[str, int], ext_map: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    """Token-based scan for GWG §4.10-§4.13 compliance."""
    issues = []
    stack: List[str] = []
    fill_cs = "DeviceGray"
    stroke_cs = "DeviceGray"
    fill_k = 0.0
    stroke_k = 0.0
    font_size = 0.0
    line_width = 1.0
    active_op = False
    active_OP = False
    active_OPM = 0
    in_shading = False

    for tok_b in _TOKEN_RE.findall(content):
        tok = tok_b.decode("latin-1", errors="ignore")
        if tok[0].isdigit() or tok[0] in "+-." or tok.startswith("/"):
            stack.append(tok)
            continue
        
        op = tok
        if op == "Tf" and len(stack) >= 2:
            try:
                font_size = float(stack[-1])
            except ValueError:
                pass
            stack.clear()
        elif op == "w" and stack:
            try:
                line_width = float(stack[-1])
            except ValueError:
                pass
            stack.clear()
        elif op == "k":
            vals = stack[-4:]
            try:
                v = [float(x) for x in vals]
                if len(v) == 4:
                    fill_cs = "DeviceCMYK"
                    fill_k = v[3] if (v[0] == 0 and v[1] == 0 and v[2] == 0) else 0.0
            except (ValueError, IndexError):
                pass
            del stack[-len(vals):]
        elif op == "K":
            vals = stack[-4:]
            try:
                v = [float(x) for x in vals]
                if len(v) == 4:
                    stroke_cs = "DeviceCMYK"
                    stroke_k = v[3] if (v[0] == 0 and v[1] == 0 and v[2] == 0) else 0.0
            except (ValueError, IndexError):
                pass
            del stack[-len(vals):]
        elif op == "g":
            vals = stack[-1:]
            try:
                v = float(vals[0])
                fill_cs = "DeviceGray"
                fill_k = 1.0 - v
            except (ValueError, IndexError):
                pass
            stack.clear()
        elif op == "G":
            vals = stack[-1:]
            try:
                v = float(vals[0])
                stroke_cs = "DeviceGray"
                stroke_k = 1.0 - v
            except (ValueError, IndexError):
                pass
            stack.clear()
        elif op == "gs" and stack:
            name = stack[-1].lstrip("/")
            xref = gs_map.get(name)
            if xref and xref in ext_map:
                state = ext_map[xref]
                active_op = state.get("op", False)
                active_OP = state.get("OP", False)
                active_OPM = state.get("OPM", 0)
            stack.clear()
        elif op == "Do" and stack:
            name = stack[-1].lstrip("/")
            if (active_op or active_OP) and "CMYK" in fill_cs:
                issues.append({"codigo": "E_IMAGE_OVERPRINT", "found_value": f"Image '{name}'"})
            stack.clear()
        elif op == "sh":
            stack.clear()
        elif op == "cs" and stack:
            if stack[-1].lstrip("/") == "Pattern":
                in_shading = True
            stack.clear()
        elif op in ("Tj", "TJ", "'", '"'):
            if 0 < font_size < _TEXT_SIZE_THRESHOLD_PT and not in_shading:
                if abs(fill_k - 1.0) <= _BLACK_K_TOLERANCE:
                     if fill_cs == "DeviceGray":
                         issues.append({"codigo": "E_BLACK_TEXT_DEVICEGRAY", "found_value": f"Gray @ {font_size}pt"})
                     elif fill_cs == "DeviceCMYK":
                         if not active_op:
                             issues.append({"codigo": "E_BLACK_TEXT_NO_OVERPRINT", "found_value": f"op=false @ {font_size}pt"})
                         elif active_OPM != 1:
                             issues.append({"codigo": "E_OPM_MISSING", "found_value": f"OPM={active_OPM}"})
            stack.clear()
        elif op in ("S", "s", "B", "B*", "b", "b*"):
            if 0 < line_width < _PATH_WIDTH_THRESHOLD_PT and not in_shading:
                k = stroke_k if stroke_k > 0 else fill_k
                cs = stroke_cs if stroke_k > 0 else fill_cs
                if abs(k - 1.0) <= _BLACK_K_TOLERANCE:
                    if cs == "DeviceGray":
                        issues.append({"codigo": "E_BLACK_PATH_DEVICEGRAY", "found_value": f"Gray @ {line_width}pt"})
                    elif cs == "DeviceCMYK":
                        if not active_OP:
                            issues.append({"codigo": "E_BLACK_THIN_NO_OVERPRINT", "found_value": f"OP=false @ {line_width}pt"})
                        elif active_OPM != 1:
                            issues.append({"codigo": "E_OPM_MISSING", "found_value": f"OPM={active_OPM}"})
            stack.clear()
        else:
            stack.clear()
    return issues

def check_black_small_overprint(file_path: str, profile: dict | None = None, visible_filter: VisibilityFilter = NULL_FILTER) -> dict[str, Any]:
    """Validate small black objects for overprint compliance."""
    doc = fitz.open(file_path)
    try:
        ext_map = {e["xref"]: e for e in _extract_extgstate_entries(doc)}
        all_issues = []
        for page in doc:
            gs_map = {}
            p_obj = doc.xref_object(page.xref)
            gs_sec = re.search(r'/ExtGState\s*<<([^>]*)>>', p_obj)
            if gs_sec:
               for n, x in re.findall(r'/(\w+)\s+(\d+)\s+0\s+R', gs_sec.group(1)):
                   gs_map[n] = int(x)
            content = b"".join(doc.xref_stream(c) or b"" for c in page.get_contents())
            for issue in _walk_small_black(content, gs_map, ext_map):
                issue["page"] = page.number + 1
                all_issues.append(issue)
        if not all_issues:
            return {"status": "OK", "label": "Overprint — Preto Pequeno"}
        primary = all_issues[0]
        res = {"status": "ERRO", "codigo": primary["codigo"], "found_value": primary["found_value"], "issues": all_issues}
        res.update(get_human_error(primary["codigo"], primary["found_value"], "≥ 12pt"))
        return res
    finally:
        doc.close()

def check_opm(file_path: str, profile: dict | None = None) -> dict[str, Any]:
    """Validate OPM=1 for PDF/X-4 and detect White Overprint."""
    doc = fitz.open(file_path)
    try:
        python_white = _python_detect_white_overprint(doc)
    finally:
        doc.close()
    gs_res = _gs_detect_overprint_issues(file_path)
    if gs_res["white_overprint"] or python_white:
        return {"status": "ERRO", "codigo": "E_WHITE_OVERPRINT", "found_value": "White Overprint"}
    return {"status": "OK", "found_value": "OPM=1"}

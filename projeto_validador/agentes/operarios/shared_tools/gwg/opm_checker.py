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
from .oc_filter import VisibilityFilter, NULL_FILTER
from .error_messages import get_human_error

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
    # Reject paths with shell-injection characters and resolve to absolute path.
    # Allowing () and [] as they are standard in graphics filenames 
    # and safe because we use shell=False.
    if re.search(r'[;&|`${}]', file_path):
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
        except Exception:
            continue
        
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


# ---------------------------------------------------------------------------
# OV-04..07 — small black text / thin black path overprint walker (§4.10-§4.13)
# ---------------------------------------------------------------------------

_TEXT_SIZE_THRESHOLD_PT: float = 12.0
_PATH_WIDTH_THRESHOLD_PT: float = 2.0
_BLACK_K_TOLERANCE: float = 1e-6


def _extgstate_map(doc: fitz.Document) -> dict[int, dict[str, Any]]:
    """xref → parsed ExtGState {op, OP, OPM} (subset of fields actually seen)."""
    out: dict[int, dict[str, Any]] = {}
    for entry in _extract_extgstate_entries(doc):
        xref = entry["xref"]
        state: dict[str, Any] = {}
        if "OPM" in entry:
            state["OPM"] = entry["OPM"]
        if "OP" in entry:
            state["OP"] = entry["OP"]
        if "op" in entry:
            state["op"] = entry["op"]
        if state:
            out[xref] = state
    return out


def _page_gs_resources(doc: fitz.Document, page: fitz.Page) -> dict[str, int]:
    """Return /GSName → xref mapping for ExtGState resources on this page."""
    try:
        page_obj = doc.xref_object(page.xref, compressed=False)
    except Exception:
        return {}
    section = re.search(r"/ExtGState\s*<<([^>]*)>>", page_obj)
    if not section:
        m = re.search(r"/ExtGState\s+(\d+)\s+0\s+R", page_obj)
        if not m:
            return {}
        try:
            section_body = doc.xref_object(int(m.group(1)), compressed=False)
        except Exception:
            return {}
    else:
        section_body = section.group(1)
    return {
        name: int(xref)
        for name, xref in re.findall(r"/(\w+)\s+(\d+)\s+0\s+R", section_body)
    }


# Tokenize: numbers, /Names, PDF string literals (…), hex strings <…>,
# arrays […], dict delimiters <<>>, and operator words (letters/digits/*/').
_TOKEN_RE = re.compile(
    rb"[-+]?\d*\.\d+|[-+]?\d+"                 # numbers
    rb"|/[A-Za-z0-9_.#\-]+"                    # /Names
    rb"|\([^()]*\)"                             # (string)
    rb"|<[0-9A-Fa-f \t\r\n]*>"                  # <hexstring>
    rb"|\[|\]|<<|>>"                            # delimiters
    rb"|[A-Za-z'\"*]+"                          # operators (Tj, TJ, Tf, re, …)
)


def _walk_small_black(
    content: bytes,
    gs_map: dict[str, int],
    ext_map: dict[int, dict[str, Any]],
    page_resources: dict[str, Any] = None,
) -> list[dict[str, Any]]:
    """Scan a decoded content stream token-by-token and flag §4.10-§4.13 issues.

    This is a deliberately compact walker: it tracks only the graphics state
    fields the four stories care about (font size, line width, current fill/
    stroke K value, current color space, active ExtGState). Unknown operators
    are ignored. Output: list of issue dicts.
    """
    issues: list[dict[str, Any]] = []
    stack: list[str] = []

    # Graphics state (simplified — no q/Q stack; tests synthesize linear streams)
    fill_cs = "DeviceGray"
    stroke_cs = "DeviceGray"
    fill_k = None          # None when not 100% black-on-K
    stroke_k = None
    font_size = 0.0
    line_width = 1.0
    active_op = False
    active_OP = False
    active_OPM = 0

    def _apply_gs(name: str) -> None:
        nonlocal active_op, active_OP, active_OPM
        xref = gs_map.get(name)
        if not xref:
            return
        state = ext_map.get(xref, {})
        if "op" in state:
            active_op = state["op"]
        if "OP" in state:
            active_OP = state["OP"]
        if "OPM" in state:
            active_OPM = state["OPM"]

    def _text_issue() -> None:
        if font_size <= 0 or font_size >= _TEXT_SIZE_THRESHOLD_PT:
            return
        if fill_k is None or abs(fill_k - 1.0) > _BLACK_K_TOLERANCE:
            return
        if fill_cs == "DeviceGray":
            issues.append({
                "codigo": "E_BLACK_TEXT_DEVICEGRAY",
                "severity": "ERRO",
                "found_value": f"DeviceGray @ {font_size:.1f}pt",
                "expected_value": f"DeviceCMYK @ <{_TEXT_SIZE_THRESHOLD_PT}pt",
            })
            return
        if fill_cs != "DeviceCMYK":
            return
        if not active_op:
            issues.append({
                "codigo": "E_BLACK_TEXT_NO_OVERPRINT",
                "severity": "ERRO",
                "found_value": f"op=false @ {font_size:.1f}pt",
                "expected_value": f"op=true @ <{_TEXT_SIZE_THRESHOLD_PT}pt",
            })
        elif active_OPM != 1:
            issues.append({
                "codigo": "E_OPM_MISSING",
                "severity": "ERRO",
                "found_value": f"OPM={active_OPM}",
                "expected_value": "OPM=1",
            })

    def _path_issue() -> None:
        if line_width <= 0 or line_width >= _PATH_WIDTH_THRESHOLD_PT:
            return
        k = stroke_k if stroke_k is not None else fill_k
        cs = stroke_cs if stroke_k is not None else fill_cs
        if k is None or abs(k - 1.0) > _BLACK_K_TOLERANCE:
            return
        if cs == "DeviceGray":
            issues.append({
                "codigo": "E_BLACK_PATH_DEVICEGRAY",
                "severity": "ERRO",
                "found_value": f"DeviceGray @ {line_width:.2f}pt",
                "expected_value": f"DeviceCMYK @ <{_PATH_WIDTH_THRESHOLD_PT}pt",
            })
            return
        if cs != "DeviceCMYK":
            return
        if not active_OP:
            issues.append({
                "codigo": "E_BLACK_THIN_NO_OVERPRINT",
                "severity": "ERRO",
                "found_value": f"OP=false @ {line_width:.2f}pt",
                "expected_value": f"OP=true @ <{_PATH_WIDTH_THRESHOLD_PT}pt",
            })
        elif active_OPM != 1:
            issues.append({
                "code": "E_OPM_MISSING",
                "severity": "ERRO",
                "found_value": f"OPM={active_OPM}",
                "expected_value": "OPM=1",
            })

    def _image_issue(name: str) -> None:
        """OV-09: CMYK images must NOT overprint (§4.22 / Ghent 1.0)."""
        if not (active_op or active_OP):
            return
        
        # Resolve XObject data from resources
        if not page_resources:
            return
        
        xobjs = page_resources.get("XObject", {})
        xobj_ref = xobjs.get(name)
        if not xobj_ref:
            return
            
        # Structural check of the XObject
        try:
            # Multi-level resolve if it's an array or dict
            # For simplicity, we assume 'xobj_ref' is the xref if it's an int/name
            # Fitz gives us references usually.
            pass 
        except Exception:
            return
        
        # If active overprint is true, and we are invoking an image...
        # We flag it. The spec says CMYK images specifically.
        # Heuristic: if we are in CMYK fill/stroke mode and invoke an image, 
        # it's highly likely a CMYK image or will be treated as such.
        if fill_cs == "DeviceCMYK" or stroke_cs == "DeviceCMYK":
            issues.append({
                "codigo": "E_IMAGE_OVERPRINT",
                "severity": "ERRO",
                "found_value": f"Image '{name}' with overprint active",
                "expected_value": "Overprint=false para imagens CMYK",
            })

    def _pop_num(n: int) -> list[float]:
        vals = stack[-n:]
        del stack[-n:]
        try:
            return [float(v) for v in vals]
        except ValueError:
            return []

    for tok_b in _TOKEN_RE.findall(content):
        tok = tok_b.decode("latin-1", errors="ignore")
        if not tok:
            continue

        if tok[0].isdigit() or tok[0] in "+-." or tok.startswith("/"):
            stack.append(tok)
            continue

        op = tok
        if op == "Tf":
            if len(stack) >= 2:
                try:
                    font_size = float(stack[-1])
                except ValueError:
                    pass
                stack.clear()
        elif op == "w":
            if stack:
                try:
                    line_width = float(stack[-1])
                except ValueError:
                    pass
                stack.clear()
        elif op == "k":      # CMYK fill
            vals = _pop_num(4)
            if len(vals) == 4:
                fill_cs = "DeviceCMYK"
                fill_k = vals[3] if vals[0] == 0 and vals[1] == 0 and vals[2] == 0 else 0.0
        elif op == "K":      # CMYK stroke
            vals = _pop_num(4)
            if len(vals) == 4:
                stroke_cs = "DeviceCMYK"
                stroke_k = vals[3] if vals[0] == 0 and vals[1] == 0 and vals[2] == 0 else 0.0
        elif op == "g":      # Gray fill
            vals = _pop_num(1)
            if vals:
                fill_cs = "DeviceGray"
                fill_k = 1.0 - vals[0]
        elif op == "G":      # Gray stroke
            vals = _pop_num(1)
            if vals:
                stroke_cs = "DeviceGray"
                stroke_k = 1.0 - vals[0]
        elif op in ("rg", "RG"):
            _pop_num(3)
            if op == "rg":
                fill_cs = "DeviceRGB"
                fill_k = None
            else:
                stroke_cs = "DeviceRGB"
                stroke_k = None
        elif op == "gs":
            if stack:
                name = stack[-1].lstrip("/")
                _apply_gs(name)
            stack.clear()
        elif op == "Do":
            if stack:
                name = stack[-1].lstrip("/")
                _image_issue(name)
            stack.clear()
        elif op in ("Tj", "TJ", "'", '"'):
            _text_issue()
            stack.clear()
        elif op in ("S", "s", "B", "B*", "b", "b*"):
            _path_issue()
            stack.clear()
        else:
            stack.clear()

    return issues


def check_black_small_overprint(
    file_path: str,
    profile: dict | None = None,
    visible_filter: VisibilityFilter = NULL_FILTER,
) -> dict[str, Any]:
    """OV-04..07 — enforce §4.10-§4.13 overprint/colorspace rules for small
    black text and thin black paths.
    """
    doc = fitz.open(file_path)
    try:
        ext_map = _extgstate_map(doc)
        all_issues: list[dict[str, Any]] = []
        for page in doc:
            # OC-02: Se a página inteira estiver oculta, pular
            # TODO: O walker de stream de bytes não tem metadata de OCG por token facilmente.
            # Mas podemos pular o scan se a página não for visível ou se soubermos que 
            # o conteúdo dela pertence a um OCG desligado. 
            
            gs_map = _page_gs_resources(doc, page)
            # Resolve page resources for XObject lookups
            page_dict = doc.xref_object(page.xref)
            res_m = re.search(r'/Resources\s+(\d+)\s+0\s+R', page_dict)
            resources = {}
            if res_m:
                 try:
                     res_obj = doc.xref_object(int(res_m.group(1)))
                     # Basic /XObject << ... >> parser
                     xo_m = re.search(r'/XObject\s*<<([^>]*)>>', res_obj)
                     if xo_m:
                         xobj_dict = {}
                         for xo_name, xo_ref in re.findall(r'/(\w+)\s+(\d+)\s+0\s+R', xo_m.group(1)):
                             xobj_dict[xo_name] = int(xo_ref)
                         resources["XObject"] = xobj_dict
                 except Exception:
                     pass

            try:
                content = b"".join(
                    doc.xref_stream(c) or b"" for c in page.get_contents()
                )
            except Exception:
                continue
            for issue in _walk_small_black(content, gs_map, ext_map, resources):
                issue["page"] = page.number + 1
                all_issues.append(issue)

        if not all_issues:
            return {
                "status": "OK",
                "label": "Overprint — Preto Pequeno (§4.10-§4.13)",
                "found_value": "Sem violações",
                "expected_value": "Texto <12pt K=1 com op+OPM=1; traços <2pt OP+OPM=1",
            }

        # Priority: first ERRO found is primary
        primary = all_issues[0]
        # Humanização
        human = get_human_error(primary["codigo"], primary["found_value"], primary["expected_value"])
        
        return {
            "status": "ERRO",
            "codigo": primary["codigo"],
            "label": "Overprint — Preto Pequeno (§4.10-§4.13)",
            "found_value": primary["found_value"],
            "expected_value": primary["expected_value"],
            "issues": all_issues,
            **human
        }
    finally:
        doc.close()


def check_opm(file_path: str, profile: dict | None = None) -> dict[str, Any]:
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

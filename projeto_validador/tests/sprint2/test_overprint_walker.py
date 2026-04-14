"""
Sprint 2 — OV-04..07 content-stream walker regressions.

The walker operates on decoded content streams plus a pre-parsed ExtGState
map, so we exercise it with hand-crafted operator sequences rather than
synthesising full PDFs.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentes.operarios.shared_tools.gwg.opm_checker import _walk_small_black


def _codes(issues):
    return [i["codigo"] for i in issues]


# ---------------------------------------------------------------------------
# OV-04 — text K=1 <12pt in DeviceCMYK requires op=true + OPM=1
# ---------------------------------------------------------------------------

def test_ov04_ac1_small_black_text_no_overprint():
    content = b"BT /F1 8 Tf 0 0 0 1 k (Hi) Tj ET"
    issues = _walk_small_black(content, gs_map={}, ext_map={})
    assert "E_BLACK_TEXT_NO_OVERPRINT" in _codes(issues)


def test_ov04_ac2_large_black_text_ok():
    content = b"BT /F1 14 Tf 0 0 0 1 k (Hi) Tj ET"
    assert _walk_small_black(content, {}, {}) == []


def test_ov04_ac3_small_black_with_op_and_opm1():
    content = b"BT /GS1 gs /F1 8 Tf 0 0 0 1 k (Hi) Tj ET"
    gs_map = {"GS1": 42}
    ext_map = {42: {"op": True, "OP": True, "OPM": 1}}
    assert _walk_small_black(content, gs_map, ext_map) == []


def test_ov04_ac4_small_black_with_op_but_opm_zero():
    content = b"BT /GS1 gs /F1 8 Tf 0 0 0 1 k (Hi) Tj ET"
    gs_map = {"GS1": 42}
    ext_map = {42: {"op": True, "OP": True, "OPM": 0}}
    assert "E_OPM_MISSING" in _codes(_walk_small_black(content, gs_map, ext_map))


def test_ov04_not_100_black_is_not_subject():
    # K=0.99 → not 100% black → rule doesn't trigger.
    content = b"BT /F1 8 Tf 0 0 0 0.99 k (Hi) Tj ET"
    assert _walk_small_black(content, {}, {}) == []


# ---------------------------------------------------------------------------
# OV-05 — small black text in DeviceGray is forbidden
# ---------------------------------------------------------------------------

def test_ov05_ac1_small_black_devicegray_fails():
    content = b"BT /F1 8 Tf 0 g (Hi) Tj ET"
    assert "E_BLACK_TEXT_DEVICEGRAY" in _codes(_walk_small_black(content, {}, {}))


def test_ov05_ac3_large_black_devicegray_ok():
    content = b"BT /F1 14 Tf 0 g (Hi) Tj ET"
    assert _walk_small_black(content, {}, {}) == []


# ---------------------------------------------------------------------------
# OV-06 — thin black stroke <2pt needs OP + OPM=1
# ---------------------------------------------------------------------------

def test_ov06_ac1_thin_black_stroke_no_overprint():
    content = b"0.5 w 0 0 0 1 K 10 10 20 20 re S"
    assert "E_BLACK_THIN_NO_OVERPRINT" in _codes(_walk_small_black(content, {}, {}))


def test_ov06_ac2_thick_black_stroke_ok():
    content = b"2.5 w 0 0 0 1 K 10 10 20 20 re S"
    assert _walk_small_black(content, {}, {}) == []


def test_ov06_ac3_thin_black_stroke_with_overprint_ok():
    content = b"/GS1 gs 0.5 w 0 0 0 1 K 10 10 20 20 re S"
    gs_map = {"GS1": 7}
    ext_map = {7: {"OP": True, "OPM": 1}}
    assert _walk_small_black(content, gs_map, ext_map) == []


# ---------------------------------------------------------------------------
# OV-07 — thin black path in DeviceGray forbidden
# ---------------------------------------------------------------------------

def test_ov07_ac1_thin_black_path_devicegray():
    content = b"0.5 w 0 G 10 10 20 20 re S"
    assert "E_BLACK_PATH_DEVICEGRAY" in _codes(_walk_small_black(content, {}, {}))

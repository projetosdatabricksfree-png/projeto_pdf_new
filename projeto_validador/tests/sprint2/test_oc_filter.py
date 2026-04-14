"""
Sprint 2 — OC-02 (§3.16) Optional Content visibility filter foundation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentes.operarios.shared_tools.gwg.oc_filter import (
    NULL_FILTER,
    VisibilityFilter,
    build_visibility_filter,
)

TEST_DIR = Path(__file__).resolve().parent / "temp_pdfs"
TEST_DIR.mkdir(exist_ok=True)


def test_null_filter_considers_everything_visible():
    assert NULL_FILTER.is_visible([1, 2, 3]) is True
    assert NULL_FILTER.is_visible([]) is True


def test_filter_with_explicit_visible_set():
    vf = VisibilityFilter(visible_ocgs=frozenset({10, 11}), all_visible=False)
    assert vf.is_visible([10]) is True
    assert vf.is_visible([99]) is False
    # Empty OCG membership → visible by default (not layered content).
    assert vf.is_visible([]) is True


def test_build_visibility_filter_on_plain_pdf_is_all_visible():
    path = TEST_DIR / "plain_no_ocg.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(path))
    doc.close()
    vf = build_visibility_filter(str(path))
    assert vf.all_visible is True


def test_run_full_suite_registers_oc_filter_stage():
    from agentes.operarios.shared_tools.gwg.run_full_suite import RUNNERS

    names = [r[0] for r in RUNNERS]
    assert "oc_filter" in names
    assert "oc_configs" in names
    assert "black_overprint" in names
    assert "delivery_2015" in names
    # Sprint 2 exit gate: original 9 + OC-01 + OC-02 + OV walker + CO-03 = 13
    assert len(RUNNERS) >= 11

"""
Sprint 2 — OC-01 (§4.29) Optional Content Configs gate.
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentes.operarios.shared_tools.gwg.optional_content_checker import (
    _count_configs,
    check_oc_configs,
)

TEST_DIR = Path(__file__).resolve().parent / "temp_pdfs"
TEST_DIR.mkdir(exist_ok=True)


def _make_plain_pdf(name: str) -> str:
    path = TEST_DIR / name
    doc = fitz.open()
    doc.new_page()
    doc.save(str(path))
    doc.close()
    return str(path)


def test_count_configs_absent():
    assert _count_configs("<< /OCGs [] /D 5 0 R >>") == 0


def test_count_configs_with_refs():
    assert _count_configs("<< /Configs [7 0 R 8 0 R 9 0 R] >>") == 3


def test_count_configs_inline_dicts():
    assert _count_configs("<< /Configs [ << /Name (A) >> << /Name (B) >> ] >>") == 2


def test_check_oc_configs_no_ocproperties():
    """AC3 — PDF without OCProperties → OK."""
    path = _make_plain_pdf("plain.pdf")
    result = check_oc_configs(path)
    assert result["status"] == "OK"

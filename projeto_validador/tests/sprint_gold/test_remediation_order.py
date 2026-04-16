"""
B-04 AC3 — Unit tests for _remediation_order().

Verifies that a disordered list of error codes is always sorted into the
canonical remediation order: geometry → transparency → colour → font → resolution.
"""
from __future__ import annotations

import pytest

from workers.tasks import _REMEDIATION_ORDER, _remediation_order


# ── Canonical order ──────────────────────────────────────────────────────────

def test_already_ordered_list_is_unchanged():
    codes = [
        "G002",
        "E004",
        "E_TGROUP_CS_INVALID",
        "E_OUTPUTINTENT_MISSING",
        "E006_FORBIDDEN_COLORSPACE",
        "E008_NON_EMBEDDED_FONTS",
        "W003_BORDERLINE_RESOLUTION",
    ]
    assert _remediation_order(codes) == codes


def test_disordered_list_is_reordered_correctly():
    """B-04 AC3: a shuffled list must come out in canonical order."""
    disordered = [
        "W003_BORDERLINE_RESOLUTION",
        "E006_FORBIDDEN_COLORSPACE",
        "G002",
        "E_TGROUP_CS_INVALID",
        "E008_NON_EMBEDDED_FONTS",
        "E004",
        "E_OUTPUTINTENT_MISSING",
    ]
    result = _remediation_order(disordered)
    assert result == [
        "G002",
        "E004",
        "E_TGROUP_CS_INVALID",
        "E_OUTPUTINTENT_MISSING",
        "E006_FORBIDDEN_COLORSPACE",
        "E008_NON_EMBEDDED_FONTS",
        "W003_BORDERLINE_RESOLUTION",
    ]


def test_transparency_before_color_conversion():
    """E_TGROUP_CS_INVALID must always precede E006_FORBIDDEN_COLORSPACE."""
    codes = ["E006_FORBIDDEN_COLORSPACE", "E_TGROUP_CS_INVALID"]
    result = _remediation_order(codes)
    assert result.index("E_TGROUP_CS_INVALID") < result.index("E006_FORBIDDEN_COLORSPACE")


def test_outputintent_before_forbidden_colorspace():
    """E_OUTPUTINTENT_MISSING must precede E006_FORBIDDEN_COLORSPACE."""
    codes = ["E006_FORBIDDEN_COLORSPACE", "E_OUTPUTINTENT_MISSING"]
    result = _remediation_order(codes)
    assert result.index("E_OUTPUTINTENT_MISSING") < result.index("E006_FORBIDDEN_COLORSPACE")


def test_geometry_before_all_color_codes():
    """G002 and E004 must always come before any colour/font/resolution code."""
    codes = [
        "W003_BORDERLINE_RESOLUTION",
        "E008_NON_EMBEDDED_FONTS",
        "E006_FORBIDDEN_COLORSPACE",
        "E004",
        "G002",
    ]
    result = _remediation_order(codes)
    assert result[0] == "G002"
    assert result[1] == "E004"


def test_unknown_codes_appended_at_end():
    """Codes not in the canonical list must be appended after known ones."""
    codes = ["E999_UNKNOWN", "G002", "X_CUSTOM"]
    result = _remediation_order(codes)
    assert result[0] == "G002"
    assert set(result[1:]) == {"E999_UNKNOWN", "X_CUSTOM"}


def test_empty_list_returns_empty():
    assert _remediation_order([]) == []


def test_single_code_returned_unchanged():
    assert _remediation_order(["E008_NON_EMBEDDED_FONTS"]) == ["E008_NON_EMBEDDED_FONTS"]


def test_full_canonical_order():
    """All codes from _REMEDIATION_ORDER must sort into their exact positions."""
    import random

    shuffled = _REMEDIATION_ORDER[:]
    random.shuffle(shuffled)
    result = _remediation_order(shuffled)
    assert result == _REMEDIATION_ORDER


@pytest.mark.parametrize("pair", [
    ("G002", "E004"),
    ("E004", "E_TGROUP_CS_INVALID"),
    ("E_TGROUP_CS_INVALID", "E_OUTPUTINTENT_MISSING"),
    ("E_OUTPUTINTENT_MISSING", "E006_FORBIDDEN_COLORSPACE"),
    ("E006_FORBIDDEN_COLORSPACE", "E008_NON_EMBEDDED_FONTS"),
    ("E008_NON_EMBEDDED_FONTS", "W_COURIER_SUBSTITUTION"),
    ("W_COURIER_SUBSTITUTION", "W003_BORDERLINE_RESOLUTION"),
])
def test_adjacent_pairs_maintain_order(pair):
    """Each adjacent pair in the canonical order must always sort correctly."""
    before, after = pair
    result = _remediation_order([after, before])
    assert result == [before, after], (
        f"Expected {before!r} before {after!r}, got {result}"
    )

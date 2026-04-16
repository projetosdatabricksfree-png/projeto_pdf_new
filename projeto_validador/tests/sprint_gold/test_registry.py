"""Registry dispatch tests — no Ghostscript or ICC required."""
from __future__ import annotations

from agentes.remediadores.bleed_remediator import BleedRemediator
from agentes.remediadores.color_space_remediator import ColorSpaceRemediator
from agentes.remediadores.font_remediator import FontRemediator
from agentes.remediadores.registry import get_remediator, supported_codes
from agentes.remediadores.resolution_remediator import ResolutionRemediator
from agentes.remediadores.safety_margin_remediator import SafetyMarginRemediator
from agentes.remediadores.transparency_flattener import TransparencyFlattener


def test_registry_routes_color_space_codes():
    assert isinstance(get_remediator("E006_FORBIDDEN_COLORSPACE"), ColorSpaceRemediator)
    assert isinstance(get_remediator("E_TAC_EXCEEDED"), ColorSpaceRemediator)


def test_registry_routes_font_codes():
    assert isinstance(get_remediator("E008_NON_EMBEDDED_FONTS"), FontRemediator)
    assert isinstance(get_remediator("W_COURIER_SUBSTITUTION"), FontRemediator)


def test_registry_routes_resolution_codes():
    assert isinstance(get_remediator("W003_BORDERLINE_RESOLUTION"), ResolutionRemediator)


def test_registry_routes_geometry_codes():
    """A-07 AC1-AC2: new Sprint A geometry codes must resolve correctly."""
    assert isinstance(get_remediator("G002"), BleedRemediator)
    assert isinstance(get_remediator("E004"), SafetyMarginRemediator)


def test_registry_routes_color_space_extended_codes():
    """A-07/B-01 AC6: OutputIntent → ColorSpaceRemediator; TGroup → TransparencyFlattener."""
    assert isinstance(get_remediator("E_OUTPUTINTENT_MISSING"), ColorSpaceRemediator)
    # Sprint B: E_TGROUP_CS_INVALID is now the primary responsibility of TransparencyFlattener
    assert isinstance(get_remediator("E_TGROUP_CS_INVALID"), TransparencyFlattener)


def test_registry_returns_none_for_unknown_code():
    assert get_remediator("E999_WAT") is None


def test_supported_codes_covers_sprint_a():
    """A-07 AC5: all Sprint A error codes must appear in supported_codes()."""
    codes = supported_codes()
    assert "G002" in codes
    assert "E004" in codes
    assert "E006_FORBIDDEN_COLORSPACE" in codes
    assert "E008_NON_EMBEDDED_FONTS" in codes
    assert "W003_BORDERLINE_RESOLUTION" in codes
    assert "E_OUTPUTINTENT_MISSING" in codes
    assert "E_TGROUP_CS_INVALID" in codes


def test_supported_codes_covers_sprint_b():
    """B-01 AC6: Sprint B codes must appear in supported_codes()."""
    codes = supported_codes()
    assert "E_TGROUP_CS_INVALID" in codes
    assert "E_OUTPUTINTENT_MISSING" in codes
    assert "E006_FORBIDDEN_COLORSPACE" in codes

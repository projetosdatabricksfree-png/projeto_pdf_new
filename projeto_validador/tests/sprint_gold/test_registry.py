"""Registry dispatch tests — no Ghostscript or ICC required."""
from __future__ import annotations

from agentes.remediadores.color_space_remediator import ColorSpaceRemediator
from agentes.remediadores.font_remediator import FontRemediator
from agentes.remediadores.registry import get_remediator, supported_codes
from agentes.remediadores.resolution_remediator import ResolutionRemediator


def test_registry_routes_color_space_codes():
    assert isinstance(get_remediator("E006_FORBIDDEN_COLORSPACE"), ColorSpaceRemediator)
    assert isinstance(get_remediator("E_TAC_EXCEEDED"), ColorSpaceRemediator)


def test_registry_routes_font_codes():
    assert isinstance(get_remediator("E008_NON_EMBEDDED_FONTS"), FontRemediator)
    assert isinstance(get_remediator("W_COURIER_SUBSTITUTION"), FontRemediator)


def test_registry_routes_resolution_codes():
    assert isinstance(get_remediator("W003_BORDERLINE_RESOLUTION"), ResolutionRemediator)


def test_registry_returns_none_for_unknown_code():
    assert get_remediator("E999_WAT") is None


def test_supported_codes_covers_big_three():
    codes = supported_codes()
    assert "E006_FORBIDDEN_COLORSPACE" in codes
    assert "E008_NON_EMBEDDED_FONTS" in codes
    assert "W003_BORDERLINE_RESOLUTION" in codes

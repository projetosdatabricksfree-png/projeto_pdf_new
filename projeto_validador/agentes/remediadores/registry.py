"""
Dispatch registry: error code → Remediator class.

Adding a new remediator is a 2-line change here. Unknown codes return None,
letting the orchestrator decide whether to reject the job or pass through.
"""
from __future__ import annotations

from typing import Optional, Type

from .base import BaseRemediator
from .bleed_remediator import BleedRemediator
from .color_space_remediator import ColorSpaceRemediator
from .font_remediator import FontRemediator
from .resolution_remediator import ResolutionRemediator
from .safety_margin_remediator import SafetyMarginRemediator

_REGISTRY: dict[str, Type[BaseRemediator]] = {
    # Geometry — Sprint A
    "G002": BleedRemediator,
    "E004": SafetyMarginRemediator,
    # Color space
    "E006_FORBIDDEN_COLORSPACE": ColorSpaceRemediator,
    "E_TAC_EXCEEDED": ColorSpaceRemediator,
    "E_OUTPUTINTENT_MISSING": ColorSpaceRemediator,
    "E_TGROUP_CS_INVALID": ColorSpaceRemediator,
    "W_ICC_V4": ColorSpaceRemediator,
    # Fonts
    "E008_NON_EMBEDDED_FONTS": FontRemediator,
    "W_COURIER_SUBSTITUTION": FontRemediator,
    # Resolution
    "W003_BORDERLINE_RESOLUTION": ResolutionRemediator,
}


def get_remediator(codigo: str) -> Optional[BaseRemediator]:
    """Return an instance of the remediator for ``codigo``, or None."""
    cls = _REGISTRY.get(codigo)
    return cls() if cls else None


def supported_codes() -> tuple[str, ...]:
    return tuple(_REGISTRY.keys())

"""Compat shim — re-exports the unified GWG font checker under the legacy name."""
from __future__ import annotations

from agentes.operarios.shared_tools.gwg.font_checker import check_fonts_gwg as check_fonts_embedded

__all__ = ["check_fonts_embedded"]

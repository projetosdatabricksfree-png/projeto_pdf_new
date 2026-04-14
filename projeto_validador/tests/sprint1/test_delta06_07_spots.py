"""Sprint 1 — DELTA-06 / DELTA-07 regression: per-variant max_spot_colors.

Validates that `check_devicen` enforces the `max_spot_colors` field from the
GWG variant profile (§4.18 / §5.7 / §5.13):

- DELTA-06: CMYK-only variants (SheetCmyk, MagazineAds, WebCmyk) → 0 spots.
- DELTA-07: NewspaperAds_CMYK → 1 spot allowed; 2 is an error.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentes.operarios.shared_tools.gwg.devicen_checker import check_devicen
from agentes.operarios.shared_tools.gwg.profile_matcher import get_gwg_profile


class _FakeDoc:
    """Minimal stub exposing the subset of fitz.Document used by check_devicen."""

    def __init__(self, separations: list[tuple[str, str]]):
        # separations = list of (spot_name, alternate_space)
        self._objs = [
            f"[/Separation /{name} /{alt} 0 R]" for name, alt in separations
        ]

    def xref_length(self) -> int:
        return len(self._objs) + 1

    def xref_object(self, xref: int, compressed: bool = False) -> str:
        return self._objs[xref - 1]

    def close(self) -> None:
        pass


def _run_with_spots(spots: list[tuple[str, str]], profile_key: str):
    profile = get_gwg_profile(profile_key)
    fake = _FakeDoc(spots)
    with patch("agentes.operarios.shared_tools.gwg.devicen_checker.fitz.open", return_value=fake):
        return check_devicen("/fake.pdf", profile)


# ---------------------------------------------------------------------------
# DELTA-06: SheetCmyk_CMYK max_spot_colors = 0
# ---------------------------------------------------------------------------

def test_delta06_sheetcmyk_rejects_single_spot():
    result = _run_with_spots([("PANTONE185C", "DeviceCMYK")], "SheetCmyk_CMYK")
    assert result["status"] == "ERRO"
    assert result["codigo"] == "E_SPOT_FORBIDDEN"
    assert result["found_value"] == 1
    assert result["expected_value"] == 0


def test_delta06_sheetcmyk_zero_spots_ok():
    result = _run_with_spots([], "SheetCmyk_CMYK")
    assert result["status"] == "OK"


def test_delta06_sheetspot_allows_spots():
    """SheetSpot_CMYK+RGB allows spots — must not raise E_SPOT_FORBIDDEN."""
    result = _run_with_spots([("PANTONE185C", "DeviceCMYK")], "SheetSpot_CMYK+RGB")
    assert result.get("codigo") != "E_SPOT_FORBIDDEN"
    assert result["status"] != "ERRO"


# ---------------------------------------------------------------------------
# DELTA-07: NewspaperAds_CMYK max_spot_colors = 1
# ---------------------------------------------------------------------------

def test_delta07_newspaper_one_spot_ok():
    result = _run_with_spots([("PANTONE185C", "DeviceCMYK")], "NewspaperAds_CMYK")
    assert result["status"] == "OK"


def test_delta07_newspaper_two_spots_error():
    result = _run_with_spots(
        [("PANTONE185C", "DeviceCMYK"), ("PANTONE286C", "DeviceCMYK")],
        "NewspaperAds_CMYK",
    )
    assert result["status"] == "ERRO"
    assert result["codigo"] == "E_SPOT_EXCEEDED"
    assert result["found_value"] == 2
    assert result["expected_value"] == 1

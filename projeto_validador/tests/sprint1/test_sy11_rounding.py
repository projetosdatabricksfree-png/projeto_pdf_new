"""Sprint 1 — SY-11 regression: GWG2015 §3.15 rounding rules.

Validates `gwg_round` for all three kinds (text / image / path) at
just-below / exact / just-above boundaries, plus the unknown-kind error path.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentes.operarios.shared_tools.gwg.rounding import gwg_round


# ---------------------------------------------------------------------------
# text — 1 decimal, HALF_UP
# ---------------------------------------------------------------------------

def test_text_just_below_rounds_down():
    assert gwg_round(11.94, "text") == 11.9


def test_text_half_rounds_up():
    # §3.15: 11.95 → 12.0 so that >= 12.0 comparison succeeds
    assert gwg_round(11.95, "text") == 12.0


def test_text_just_above():
    assert gwg_round(11.96, "text") == 12.0


# ---------------------------------------------------------------------------
# image — 0 decimals, HALF_UP
# ---------------------------------------------------------------------------

def test_image_just_below_rounds_down():
    assert gwg_round(148.4, "image") == 148


def test_image_half_rounds_up():
    assert gwg_round(148.5, "image") == 149


def test_image_just_above_ceiling():
    # 148.7 → 149 → passes a >= 149 check (per SY-11 AC2 inverse reading)
    assert gwg_round(148.7, "image") == 149


# ---------------------------------------------------------------------------
# path — 3 decimals, HALF_UP
# ---------------------------------------------------------------------------

def test_path_just_below():
    assert gwg_round(0.2494, "path") == 0.249


def test_path_half_rounds_up():
    assert gwg_round(0.2495, "path") == 0.250


def test_path_just_above():
    assert gwg_round(0.2496, "path") == 0.250


# ---------------------------------------------------------------------------
# Error path
# ---------------------------------------------------------------------------

def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        gwg_round(1.0, "bogus")  # type: ignore[arg-type]

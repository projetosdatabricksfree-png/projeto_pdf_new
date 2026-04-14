"""
Sprint 2 — CO-03 §4.24 Delivery Method colour-space matrix.

Validates the allow/deny matrix literally from §4.24 for the *_CMYK+RGB
variants. Uses the classification helpers directly (no full PDF synthesis).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentes.operarios.shared_tools.gwg.color_checker import (
    _FORBIDDEN_ALTERNATE_2015,
    _FORBIDDEN_IMAGE_2015,
    _FORBIDDEN_NON_IMAGE_2015,
    _variant_is_rgb_delivery,
)
from agentes.operarios.shared_tools.gwg.profile_matcher import GWG_PROFILES


# bucket, colorspace, expected_forbidden
_MATRIX = [
    ("image",     "DeviceCMYK",    False),
    ("image",     "DeviceRGB",     True),
    ("image",     "CalGray",       True),
    ("image",     "ICCBasedGray",  True),
    ("image",     "ICCBasedCMYK",  True),
    ("non_image", "DeviceCMYK",    False),
    ("non_image", "Lab",           True),
    ("non_image", "DeviceRGB",     True),
    ("alternate", "DeviceCMYK",    False),
    ("alternate", "DeviceRGB",     True),
]


@pytest.mark.parametrize("bucket,cs,forbidden", _MATRIX)
def test_co03_matrix(bucket: str, cs: str, forbidden: bool):
    buckets = {
        "image": _FORBIDDEN_IMAGE_2015,
        "non_image": _FORBIDDEN_NON_IMAGE_2015,
        "alternate": _FORBIDDEN_ALTERNATE_2015,
    }
    assert (cs in buckets[bucket]) is forbidden


def test_co03_rgb_variant_detection():
    assert _variant_is_rgb_delivery(GWG_PROFILES["MagazineAds_CMYK+RGB"])
    assert not _variant_is_rgb_delivery(GWG_PROFILES["MagazineAds_CMYK"])

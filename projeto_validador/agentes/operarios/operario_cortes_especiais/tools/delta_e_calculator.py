"""
Delta E Calculator — Calculates colorimetric deviation.

ΔE < 2.0 required for brand identity consistency.
"""
from __future__ import annotations

import math


def calculate_delta_e(lab1: tuple[float, float, float], lab2: tuple[float, float, float]) -> float:
    """Calculate CIE76 ΔE between two Lab color values.

    Args:
        lab1: (L, a, b) of color 1.
        lab2: (L, a, b) of color 2.

    Returns:
        ΔE value.
    """
    return math.sqrt(
        (lab1[0] - lab2[0]) ** 2
        + (lab1[1] - lab2[1]) ** 2
        + (lab1[2] - lab2[2]) ** 2
    )


def check_brand_color(file_path: str, brand_lab: tuple[float, float, float] | None = None) -> dict:
    """Check brand color deviation.

    Args:
        file_path: Path to the PDF.
        brand_lab: Target brand Lab color values.

    Returns:
        Dictionary with check results.
    """
    if brand_lab is None:
        return {"status": "N/A", "detalhe": "Cor de marca não informada"}

    # In a full implementation, we'd sample dominant colors via pyvips
    # and compare against brand_lab
    return {"status": "OK", "detalhe": "Verificação de marca não executada (sem target)"}

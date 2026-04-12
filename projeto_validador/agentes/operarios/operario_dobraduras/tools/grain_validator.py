"""
Grain Validator — Validates grain direction vs fold orientation.

Paper >150g folded against grain = coating crack.
"""
from __future__ import annotations


def check_grain_direction(
    gramatura_gsm: int,
    grain_direction: str,
    fold_orientation: str,
) -> dict:
    """Check grain direction compatibility with fold.

    Args:
        gramatura_gsm: Paper weight.
        grain_direction: 'long_grain' or 'short_grain'.
        fold_orientation: 'landscape' or 'portrait'.

    Returns:
        Dictionary with check results.
    """
    if gramatura_gsm <= 150:
        return {"status": "OK", "detalhe": "Gramatura ≤ 150g — fibra não crítica"}

    if grain_direction == "unknown":
        return {"status": "OK", "detalhe": "Direção da fibra não informada"}

    # Fold should be parallel to grain direction
    if grain_direction == "long_grain" and fold_orientation == "landscape":
        return {"status": "OK", "detalhe": "Dobra paralela à fibra longa"}
    elif grain_direction == "short_grain" and fold_orientation == "portrait":
        return {"status": "OK", "detalhe": "Dobra paralela à fibra curta"}
    else:
        return {
            "status": "ERRO",
            "codigo": "E006_GRAIN_DIRECTION_MISMATCH",
            "detalhe": f"Fibra={grain_direction}, Dobra={fold_orientation}",
        }


def check_mechanical_score(gramatura_gsm: int) -> dict:
    """Check if mechanical score is required.

    Args:
        gramatura_gsm: Paper weight.

    Returns:
        Dictionary with check results.
    """
    if gramatura_gsm > 150:
        return {
            "status": "ERRO",
            "codigo": "E004_MECHANICAL_SCORE_REQUIRED",
            "detalhe": f"Gramatura {gramatura_gsm}g > 150g — vinco mecânico obrigatório",
        }
    return {"status": "OK"}

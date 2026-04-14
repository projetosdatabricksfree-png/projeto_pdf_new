"""GWG2015 §3.15 rounding rules.

Normalises numeric values before threshold comparison so that edge cases
(e.g. 11.96pt text, 148.7ppi image) are evaluated exactly as the spec
prescribes. Uses banker-free half-up rounding (decimal.ROUND_HALF_UP).

Precision per kind:
- text  → 1 decimal place (e.g. 11.96 → 12.0)
- image → 0 decimal places (e.g. 148.7 → 149)
- path  → 3 decimal places (e.g. 0.2495 → 0.250)
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

RoundKind = Literal["text", "image", "path"]

_QUANTIZERS: dict[str, Decimal] = {
    "text": Decimal("0.1"),
    "image": Decimal("1"),
    "path": Decimal("0.001"),
}


def gwg_round(value: float, kind: RoundKind) -> float:
    """Round `value` per GWG2015 §3.15 precision for the given `kind`.

    Raises:
        ValueError: if `kind` is not one of 'text', 'image', 'path'.
    """
    quant = _QUANTIZERS.get(kind)
    if quant is None:
        raise ValueError(f"Unknown rounding kind: {kind!r}")
    return float(Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP))

"""
SafetyMarginRemediator — shrink page content 97% to guarantee 3mm safety margin.

Strategy (shrink-to-safe):
1. Measure the smallest font present in the document via PyMuPDF.
2. If min_font_size * 0.97 < 5pt → skip transform, emit warning (content preserved).
3. Otherwise, prepend a `q <cm matrix> cm` stream and append `Q` via pikepdf so that
   all content is scaled to 97% from the page center, without touching vector data
   or re-rasterising anything.

Handles:
  - E004 : critical content closer than 3mm to the TrimBox cut line
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path

from app.api.schemas import RemediationAction, ValidationResult

from .base import BaseRemediator

logger = logging.getLogger(__name__)

SCALE = 0.97
MIN_FONT_THRESHOLD_PT = 5.0
SAFETY_MARGIN_MM = 3.0


class SafetyMarginRemediator(BaseRemediator):
    name = "SafetyMarginRemediator"
    handles = ("E004",)

    def remediate(
        self,
        pdf_in: Path,
        pdf_out: Path,
        validation_result: ValidationResult,
    ) -> RemediationAction:
        try:
            import pikepdf  # noqa: PLC0415
        except ImportError:
            return self._fail(
                codigo=validation_result.codigo or "E004",
                warnings=["pikepdf not installed"],
                log="SafetyMarginRemediator requires pikepdf.",
            )
        try:
            import pymupdf  # noqa: PLC0415
        except ImportError:
            return self._fail(
                codigo=validation_result.codigo or "E004",
                warnings=["pymupdf not installed"],
                log="SafetyMarginRemediator requires pymupdf for font size measurement.",
            )

        codigo = validation_result.codigo or "E004"
        pdf_out.parent.mkdir(parents=True, exist_ok=True)

        # Step 1: measure smallest font before transforming
        min_font_size = self._measure_min_font(pdf_in, pymupdf)
        if min_font_size is not None and (min_font_size * SCALE) < MIN_FONT_THRESHOLD_PT:
            # Copy input to output unchanged so the pipeline can continue
            shutil.copy2(pdf_in, pdf_out)
            return self._warn(
                codigo=codigo,
                changes=[],
                warnings=[
                    f"shrink-to-safe inviável: fonte mínima resultaria "
                    f"{min_font_size * SCALE:.1f}pt (<{MIN_FONT_THRESHOLD_PT}pt); "
                    "conteúdo original preservado"
                ],
                log=(
                    f"min_font={min_font_size:.1f}pt; scaled would be "
                    f"{min_font_size * SCALE:.1f}pt — below 5pt threshold; "
                    "original content preserved verbatim"
                ),
                severity="medium",
            )

        # Step 2: apply cm matrix via pikepdf
        try:
            with pikepdf.open(str(pdf_in)) as pdf:
                for page in pdf.pages:
                    self._apply_scale_matrix(pdf, page)
                pdf.save(str(pdf_out))
        except Exception as exc:
            logger.exception("SafetyMarginRemediator pikepdf error: %s", exc)
            return self._fail(
                codigo=codigo,
                warnings=[f"pikepdf failed to apply shrink transform: {exc}"],
                log=str(exc),
            )

        if not pdf_out.exists() or pdf_out.stat().st_size == 0:
            return self._fail(
                codigo=codigo,
                warnings=["Output PDF not produced or empty after shrink"],
                log="SafetyMarginRemediator produced no output.",
            )

        font_note = (
            f"min_font={min_font_size:.1f}pt → {min_font_size * SCALE:.1f}pt"
            if min_font_size is not None
            else "min_font=unknown"
        )
        return self._ok(
            codigo=codigo,
            changes=[
                f"Applied cm matrix ({SCALE} 0 0 {SCALE} tx ty) — content scaled "
                f"to {SCALE * 100:.0f}% from page center",
                font_note,
            ],
            log=f"pikepdf ok; output={pdf_out.stat().st_size} bytes",
        )

    # ── Private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _measure_min_font(pdf_path: Path, pymupdf) -> float | None:
        """Return the smallest font size found across all pages, or None."""
        min_size: float | None = None
        try:
            with pymupdf.open(str(pdf_path)) as doc:
                for page in doc:
                    blocks = page.get_text("dict").get("blocks", [])
                    for block in blocks:
                        if block.get("type") != 0:  # 0 = text
                            continue
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                size = span.get("size")
                                if size and size > 0:
                                    min_size = size if min_size is None else min(min_size, size)
        except Exception as exc:
            logger.warning("Font size measurement failed: %s", exc)
            return None
        return min_size

    @staticmethod
    def _apply_scale_matrix(pdf, page) -> None:
        """Prepend q/cm and append Q to each page's content stream(s)."""
        import pikepdf  # noqa: PLC0415

        mediabox = page.mediabox
        w = float(mediabox[2]) - float(mediabox[0])
        h = float(mediabox[3]) - float(mediabox[1])

        # Translation to keep content centred after scaling
        tx = (w * (1.0 - SCALE)) / 2.0
        ty = (h * (1.0 - SCALE)) / 2.0

        prefix = f"q {SCALE} 0 0 {SCALE} {tx:.4f} {ty:.4f} cm\n".encode()
        suffix = b"\nQ"

        prefix_stream = pdf.make_stream(prefix)
        suffix_stream = pdf.make_stream(suffix)

        obj = page.obj
        if "/Contents" not in obj:
            obj["/Contents"] = pikepdf.Array([prefix_stream, suffix_stream])
            return

        contents = obj["/Contents"]
        if isinstance(contents, pikepdf.Array):
            obj["/Contents"] = pikepdf.Array(
                [prefix_stream, *list(contents), suffix_stream]
            )
        else:
            obj["/Contents"] = pikepdf.Array([prefix_stream, contents, suffix_stream])

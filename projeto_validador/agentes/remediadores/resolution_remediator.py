"""
ResolutionRemediator — downsample oversized raster images; upsample if below target.

Strategy:
- Images *above* 450 dpi: downsampled via Ghostscript bicubic to 300 dpi (lossless quality).
- Images *below* 300 dpi: upsampled via Ghostscript bicubic to 300 dpi with a
  quality_loss_warning. Upsampling invents pixels, but delivering a slightly blurry
  file is better than blocking the job — the warning tells the designer to resupply.

Contract (post-Sprint A): success=True whenever Ghostscript completes, even for
upsampling. success=False only for technical failures (binary missing, timeout).

Handles:
  - W003_BORDERLINE_RESOLUTION : images outside the 300–450 dpi acceptable range.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from app.api.schemas import RemediationAction, ValidationResult

from .base import BaseRemediator

logger = logging.getLogger(__name__)

TARGET_DPI = 300
DOWNSAMPLE_THRESHOLD = 450  # only touch images meaningfully above target


class ResolutionRemediator(BaseRemediator):
    name = "ResolutionRemediator"
    handles = ("W003_BORDERLINE_RESOLUTION",)

    def __init__(self, gs_binary: str = "gs") -> None:
        self.gs_binary = gs_binary

    def remediate(
        self,
        pdf_in: Path,
        pdf_out: Path,
        validation_result: ValidationResult,
    ) -> RemediationAction:
        codigo = validation_result.codigo or "W003_BORDERLINE_RESOLUTION"

        found_dpi = self._parse_dpi(validation_result.found_value)
        needs_upsample = found_dpi is not None and found_dpi < TARGET_DPI

        if shutil.which(self.gs_binary) is None:
            return self._fail(
                codigo=codigo,
                warnings=[f"Ghostscript binary '{self.gs_binary}' not on PATH"],
                log="Ghostscript is required for image downsampling.",
            )

        pdf_out.parent.mkdir(parents=True, exist_ok=True)

        if needs_upsample:
            # Upsample: force all color/gray images to TARGET_DPI regardless of source DPI.
            # Threshold=0.9 ensures images at any DPI (including < 300) get resampled.
            cmd = [
                self.gs_binary,
                "-dBATCH", "-dNOPAUSE", "-dSAFER", "-dQUIET",
                "-sDEVICE=pdfwrite",
                "-dPDFSETTINGS=/prepress",
                "-dCompatibilityLevel=1.6",
                "-dDownsampleColorImages=true",
                "-dUpsampleColorImages=true",
                f"-dColorImageResolution={TARGET_DPI}",
                "-dColorImageDownsampleThreshold=0.900",
                "-dColorImageDownsampleType=/Bicubic",
                "-dDownsampleGrayImages=true",
                "-dUpsampleGrayImages=true",
                f"-dGrayImageResolution={TARGET_DPI}",
                "-dGrayImageDownsampleThreshold=0.900",
                "-dGrayImageDownsampleType=/Bicubic",
                f"-sOutputFile={pdf_out}",
                str(pdf_in),
            ]
        else:
            # Downsample only: only touch images significantly above target.
            cmd = [
                self.gs_binary,
                "-dBATCH", "-dNOPAUSE", "-dSAFER", "-dQUIET",
                "-sDEVICE=pdfwrite",
                "-dPDFSETTINGS=/prepress",
                "-dCompatibilityLevel=1.6",
                "-dDownsampleColorImages=true",
                f"-dColorImageResolution={TARGET_DPI}",
                f"-dColorImageDownsampleThreshold={DOWNSAMPLE_THRESHOLD / TARGET_DPI:.3f}",
                "-dColorImageDownsampleType=/Bicubic",
                "-dDownsampleGrayImages=true",
                f"-dGrayImageResolution={TARGET_DPI}",
                f"-dGrayImageDownsampleThreshold={DOWNSAMPLE_THRESHOLD / TARGET_DPI:.3f}",
                "-dGrayImageDownsampleType=/Bicubic",
                "-dDownsampleMonoImages=true",
                "-dMonoImageResolution=1200",
                "-dMonoImageDownsampleType=/Subsample",
                f"-sOutputFile={pdf_out}",
                str(pdf_in),
            ]

        try:
            result = subprocess.run(
                cmd, check=False, capture_output=True, text=True, timeout=300
            )
        except subprocess.TimeoutExpired:
            return self._fail(
                codigo=codigo,
                warnings=["Ghostscript timeout (>300s)"],
                log="Downsampling exceeded time budget.",
            )

        if result.returncode != 0 or not pdf_out.exists():
            return self._fail(
                codigo=codigo,
                warnings=["Ghostscript returned non-zero during downsampling"],
                log=f"stderr={result.stderr[-800:]!r}",
            )

        if needs_upsample:
            return self._warn(
                codigo=codigo,
                changes=[
                    f"Upsampled color/gray images from {found_dpi} dpi to "
                    f"{TARGET_DPI} dpi (bicubic Ghostscript)",
                ],
                warnings=[
                    f"upsampled from {found_dpi}dpi to {TARGET_DPI}dpi (bicubic): "
                    "designer should resupply higher-resolution source"
                ],
                log=f"gs ok (upsample); output={pdf_out.stat().st_size} bytes",
                severity="medium",
            )

        return self._ok(
            codigo=codigo,
            changes=[
                f"Downsampled color/gray images >{DOWNSAMPLE_THRESHOLD} dpi "
                f"to {TARGET_DPI} dpi (bicubic)",
                "Mono images capped at 1200 dpi",
            ],
            log=f"gs ok; output={pdf_out.stat().st_size} bytes",
        )

    @staticmethod
    def _parse_dpi(found_value: str | None) -> int | None:
        if not found_value:
            return None
        import re
        match = re.search(r"(\d+)\s*dpi", found_value, re.IGNORECASE)
        return int(match.group(1)) if match else None

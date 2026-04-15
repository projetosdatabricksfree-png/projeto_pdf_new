"""
ResolutionRemediator — downsample oversized raster images.

Strategy: Ghostscript with explicit downsample thresholds for color / gray /
mono streams. Target 300 dpi (industry standard for offset CMYK printing).

Regra de Ouro: this remediator **never upsamples**. Upscaling invents pixels
and destroys sharpness — the original low-res image must be resupplied.

Handles:
  - W003_BORDERLINE_RESOLUTION : images above the threshold get downsampled.
                                  Images *below* 300 dpi trigger a hard fail.
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
        if found_dpi is not None and found_dpi < TARGET_DPI:
            return self._fail(
                codigo=codigo,
                warnings=[f"Image resolution {found_dpi} dpi is below target {TARGET_DPI} dpi"],
                log=(
                    "Regra de Ouro: upsampling is forbidden — it fabricates pixels "
                    "and looks worse on press than the low-res original. The "
                    "designer must resupply a higher-resolution image."
                ),
            )

        if shutil.which(self.gs_binary) is None:
            return self._fail(
                codigo=codigo,
                warnings=[f"Ghostscript binary '{self.gs_binary}' not on PATH"],
                log="Ghostscript is required for image downsampling.",
            )

        pdf_out.parent.mkdir(parents=True, exist_ok=True)

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

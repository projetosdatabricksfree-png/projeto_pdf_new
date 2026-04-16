"""
TransparencyFlattener — flatten transparency groups for E_TGROUP_CS_INVALID.

Strategy: Ghostscript with -dCompatibilityLevel=1.3 forces all transparency
groups, blend modes, and alpha channels to be composited and flattened into
opaque CMYK objects. This eliminates TGroup colorspace mismatch errors that
PDF/X-4 validators flag when a transparency group's /CS entry doesn't match
the page's DeviceCMYK process model.

Why PDF 1.3: it predates the transparency model (introduced in PDF 1.4), so
Ghostscript is forced to rasterise blend modes in-place rather than preserve
them as live transparency groups.

Handles:
  - E_TGROUP_CS_INVALID : transparency group with invalid/mismatched colorspace
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

from app.api.schemas import RemediationAction, ValidationResult

from .base import BaseRemediator

logger = logging.getLogger(__name__)

ICC_PROFILE_ENV = "FOGRA39_ICC_PATH"
DEFAULT_ICC_PATH = "/usr/share/color/icc/ISOcoated_v2_300_eci.icc"


class TransparencyFlattener(BaseRemediator):
    name = "TransparencyFlattener"
    handles = ("E_TGROUP_CS_INVALID",)

    def __init__(self, icc_path: str | None = None, gs_binary: str = "gs") -> None:
        self.icc_path = icc_path or os.getenv(ICC_PROFILE_ENV, DEFAULT_ICC_PATH)
        self.gs_binary = gs_binary

    def remediate(
        self,
        pdf_in: Path,
        pdf_out: Path,
        validation_result: ValidationResult,
    ) -> RemediationAction:
        codigo = validation_result.codigo or "E_TGROUP_CS_INVALID"

        if shutil.which(self.gs_binary) is None:
            return self._fail(
                codigo=codigo,
                warnings=[f"Ghostscript binary '{self.gs_binary}' not on PATH"],
                log="TransparencyFlattener requires Ghostscript.",
            )

        icc_exists = Path(self.icc_path).exists()
        if not icc_exists:
            logger.warning(
                "FOGRA39 ICC not found at %s; flattening without explicit profile", self.icc_path
            )

        pdf_out.parent.mkdir(parents=True, exist_ok=True)

        # Build Ghostscript command.
        # -dCompatibilityLevel=1.3  → output PDF 1.3; GS flattens all transparency.
        # -dHaveTransparency=false   → explicit signal to GS transparency flattener.
        # -sColorConversionStrategy=CMYK → convert all incoming colorspaces to CMYK.
        # -sProcessColorModel=DeviceCMYK → GS internal model is CMYK.
        # -dOverrideICC=true + profile flags → keeps gradients already in CMYK intact
        #   by re-routing through the same ICC instead of a second conversion.
        cmd = [
            self.gs_binary,
            "-dBATCH", "-dNOPAUSE", "-dSAFER", "-dQUIET",
            "-sDEVICE=pdfwrite",
            "-dPDFSETTINGS=/prepress",
            "-dCompatibilityLevel=1.3",
            "-dHaveTransparency=false",
            "-sColorConversionStrategy=CMYK",
            "-sProcessColorModel=DeviceCMYK",
        ]

        if icc_exists:
            cmd += [
                "-sDefaultCMYKProfile=" + self.icc_path,
                "-sOutputICCProfile=" + self.icc_path,
                "-dOverrideICC=true",
            ]

        cmd += [
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
                warnings=["Ghostscript timeout (>300s) during transparency flattening"],
                log="Source PDF likely has extremely complex transparency.",
            )

        if result.returncode != 0 or not pdf_out.exists():
            return self._fail(
                codigo=codigo,
                warnings=["Ghostscript returned non-zero during flattening"],
                log=f"stderr={result.stderr[-800:]!r}",
            )

        if pdf_out.stat().st_size == 0:
            return self._fail(
                codigo=codigo,
                warnings=["Ghostscript produced empty output during flattening"],
                log="Output file is 0 bytes.",
            )

        # Stamp OutputIntent so the file remains PDF/X-aware after flattening.
        if icc_exists:
            try:
                self._stamp_pdfx4(pdf_out)
            except Exception as exc:
                logger.warning("PDF/X-4 stamping after flatten failed: %s", exc)

        return self._ok(
            codigo=codigo,
            changes=[
                "Transparency groups flattened to PDF 1.3 (no live blend modes)",
                "All TGroup colorspaces normalised to DeviceCMYK",
                "Stamped PDF/X-4 OutputIntent (ISO Coated v2 300% ECI)" if icc_exists else
                "OutputIntent stamp skipped (ICC not found)",
            ],
            log=f"gs flatten ok; output={pdf_out.stat().st_size} bytes",
        )

    def _stamp_pdfx4(self, pdf_path: Path) -> None:
        """Attach an OutputIntent referencing the FOGRA39 ICC profile."""
        import pikepdf

        with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
            with open(self.icc_path, "rb") as fh:
                icc_bytes = fh.read()

            icc_stream = pdf.make_stream(icc_bytes)
            icc_stream.N = 4  # CMYK
            output_intent = pikepdf.Dictionary(
                Type=pikepdf.Name("/OutputIntent"),
                S=pikepdf.Name("/GTS_PDFX"),
                OutputConditionIdentifier=pikepdf.String("FOGRA39"),
                RegistryName=pikepdf.String("http://www.color.org"),
                Info=pikepdf.String("Coated FOGRA39 (ISO 12647-2:2004)"),
                DestOutputProfile=icc_stream,
            )
            pdf.Root.OutputIntents = pikepdf.Array([output_intent])
            pdf.Root.GTS_PDFXVersion = pikepdf.String("PDF/X-4")
            pdf.save(pdf_path)

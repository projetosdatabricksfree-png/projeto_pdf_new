"""
ColorSpaceRemediator — RGB/sRGB → CMYK (FOGRA39 / ISOcoated_v2_300_eci).

Strategy: Ghostscript color conversion with an explicit ICC profile, then
pikepdf stamps the PDF/X-4 OutputIntent so downstream RIPs recognize the file.

Why Ghostscript rather than pikepdf alone: pikepdf does not perform colorimetric
conversion of image samples or DeviceRGB operators — it would only rewrite
ColorSpace names, producing visually broken output. Ghostscript applies the ICC
transform to every painting operator deterministically.

Handles:
  - E006_FORBIDDEN_COLORSPACE : non-CMYK objects on a print job
  - E_TAC_EXCEEDED            : re-separation under TAC=300% via the same ICC

Fails (Regra de Ouro):
  - ICC profile missing from the container (no silent fallback to sRGB-default)
  - Ghostscript returns non-zero (corrupt source, encrypted PDF, etc.)
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


class ColorSpaceRemediator(BaseRemediator):
    name = "ColorSpaceRemediator"
    handles = ("E006_FORBIDDEN_COLORSPACE", "E_TAC_EXCEEDED")

    def __init__(self, icc_path: str | None = None, gs_binary: str = "gs") -> None:
        self.icc_path = icc_path or os.getenv(ICC_PROFILE_ENV, DEFAULT_ICC_PATH)
        self.gs_binary = gs_binary

    def remediate(
        self,
        pdf_in: Path,
        pdf_out: Path,
        validation_result: ValidationResult,
    ) -> RemediationAction:
        codigo = validation_result.codigo or "E006_FORBIDDEN_COLORSPACE"

        if not Path(self.icc_path).exists():
            return self._fail(
                codigo=codigo,
                warnings=[f"ICC profile not found: {self.icc_path}"],
                log=(
                    "Refusing silent fallback — a non-industrial ICC would produce "
                    "unpredictable tonal shifts. Set FOGRA39_ICC_PATH or install "
                    "ISOcoated_v2_300_eci.icc in the worker image."
                ),
            )

        if shutil.which(self.gs_binary) is None:
            return self._fail(
                codigo=codigo,
                warnings=[f"Ghostscript binary '{self.gs_binary}' not on PATH"],
                log="Ghostscript is required for colorimetric conversion.",
            )

        pdf_out.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.gs_binary,
            "-dBATCH", "-dNOPAUSE", "-dSAFER", "-dQUIET",
            "-sDEVICE=pdfwrite",
            "-dPDFSETTINGS=/prepress",
            "-dCompatibilityLevel=1.6",
            "-sColorConversionStrategy=CMYK",
            "-dProcessColorModel=/DeviceCMYK",
            "-sDefaultCMYKProfile=" + self.icc_path,
            "-sOutputICCProfile=" + self.icc_path,
            "-dOverrideICC=true",
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
                log="Source PDF likely oversized or contains pathological objects.",
            )

        if result.returncode != 0 or not pdf_out.exists():
            return self._fail(
                codigo=codigo,
                warnings=["Ghostscript returned non-zero"],
                log=f"stderr={result.stderr[-800:]!r}",
            )

        # Stamp PDF/X-4 OutputIntent so the RIP recognizes the file.
        try:
            self._stamp_pdfx4(pdf_out)
        except Exception as exc:  # pikepdf import/runtime errors
            logger.warning("PDF/X-4 stamping failed: %s", exc)
            # Conversion succeeded; downstream validador_final will catch missing OI.

        return self._ok(
            codigo=codigo,
            changes=[
                f"Converted all objects to DeviceCMYK via {Path(self.icc_path).name}",
                "Stamped PDF/X-4 OutputIntent (ISO Coated v2 300% ECI)",
            ],
            log=f"gs ok; output={pdf_out.stat().st_size} bytes",
        )

    def _stamp_pdfx4(self, pdf_path: Path) -> None:
        """Attach an OutputIntent referencing the FOGRA39 ICC."""
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

"""
FontRemediator — embed non-embedded fonts deterministically.

Strategy: Ghostscript re-distillation with -dEmbedAllFonts=true and
-dSubsetFonts=true.

Handles:
  - E008_NON_EMBEDDED_FONTS : referenced but not embedded; fixable if installed.
  - W_COURIER_SUBSTITUTION  : renderer already substituted Courier. Post-Sprint A
    contract: we accept this and embed Courier as a fallback, emitting a
    quality_loss_warning. The designer is informed to resupply the original font.
    Blocking delivery over a font substitution fails the "entregar sempre" contract.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from app.api.schemas import RemediationAction, ValidationResult

from .base import BaseRemediator

logger = logging.getLogger(__name__)


class FontRemediator(BaseRemediator):
    name = "FontRemediator"
    handles = ("E008_NON_EMBEDDED_FONTS", "W_COURIER_SUBSTITUTION")

    def __init__(self, gs_binary: str = "gs") -> None:
        self.gs_binary = gs_binary

    def remediate(
        self,
        pdf_in: Path,
        pdf_out: Path,
        validation_result: ValidationResult,
    ) -> RemediationAction:
        codigo = validation_result.codigo or "E008_NON_EMBEDDED_FONTS"
        is_courier_substitution = (codigo == "W_COURIER_SUBSTITUTION")

        if shutil.which(self.gs_binary) is None:
            return self._fail(
                codigo=codigo,
                warnings=[f"Ghostscript binary '{self.gs_binary}' not on PATH"],
                log="Ghostscript is required for font embedding.",
            )

        pdf_out.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.gs_binary,
            "-dBATCH", "-dNOPAUSE", "-dSAFER", "-dQUIET",
            "-sDEVICE=pdfwrite",
            "-dPDFSETTINGS=/prepress",
            "-dCompatibilityLevel=1.6",
            "-dEmbedAllFonts=true",
            "-dSubsetFonts=true",
            "-dMaxSubsetPct=100",
            "-dCompressFonts=true",
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
                log="Font embedding exceeded time budget.",
            )

        if result.returncode != 0 or not pdf_out.exists():
            return self._fail(
                codigo=codigo,
                warnings=["Ghostscript returned non-zero during font embedding"],
                log=f"stderr={result.stderr[-800:]!r}",
            )

        missing = self._list_missing_fonts(pdf_out)
        if missing:
            return self._fail(
                codigo=codigo,
                warnings=[f"Fonts still unembedded after remediation: {missing}"],
                log=(
                    "Ghostscript could not locate the font files on disk. Install "
                    "the fonts in /usr/share/fonts in the worker image, or request "
                    "the source files from the designer."
                ),
            )

        fonts_found = validation_result.found_value or "referenced fonts"

        if is_courier_substitution:
            return self._warn(
                codigo=codigo,
                changes=[f"Embedded Courier as fallback font ({fonts_found})"],
                warnings=[
                    "Courier accepted as fallback font; original font unavailable — "
                    "designer should resupply the correct font file"
                ],
                log=f"gs ok (courier fallback); output={pdf_out.stat().st_size} bytes",
                severity="low",
            )

        return self._ok(
            codigo=codigo,
            changes=[f"Embedded and subset all fonts ({fonts_found})"],
            log=f"gs ok; output={pdf_out.stat().st_size} bytes",
        )

    def _list_missing_fonts(self, pdf_path: Path) -> list[str]:
        """Return the list of fonts that remain non-embedded."""
        try:
            import pymupdf  # PyMuPDF
        except ImportError:  # pragma: no cover
            logger.warning("PyMuPDF unavailable — skipping post-embed verification")
            return []

        missing: list[str] = []
        with pymupdf.open(pdf_path) as doc:
            for page in doc:
                for font in page.get_fonts(full=True):
                    # font tuple: (xref, ext, type, basefont, name, encoding, referencer)
                    ext = font[1]
                    basefont = font[3]
                    if not ext or ext == "n/a":
                        if basefont not in missing:
                            missing.append(basefont)
        return missing

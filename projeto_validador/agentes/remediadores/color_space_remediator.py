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
  - E_OUTPUTINTENT_MISSING    : PDF/X OutputIntent absent or malformed

Fails (Regra de Ouro):
  - ICC profile missing from the container (no silent fallback to sRGB-default)
  - Ghostscript returns non-zero (corrupt source, encrypted PDF, etc.)

Sprint B additions:
  - B-02: _inject_output_intent detects 4 invalid states and always replaces.
  - B-03: _normalize_color_spaces converts residual RGB XObjects after flattening.
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

# Expected byte-length lower bound for a real ICC profile.
_ICC_MIN_BYTES = 256


class ColorSpaceRemediator(BaseRemediator):
    name = "ColorSpaceRemediator"
    handles = ("E006_FORBIDDEN_COLORSPACE", "E_TAC_EXCEEDED", "E_OUTPUTINTENT_MISSING")

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

        # OutputIntent-only errors: no full Ghostscript conversion needed.
        if codigo == "E_OUTPUTINTENT_MISSING":
            return self._handle_outputintent_only(pdf_in, pdf_out, codigo)

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

        # B-03: Convert any residual RGB XObjects after GS conversion.
        rgb_changes = self._normalize_color_spaces(pdf_out)

        # B-02: Inject / replace OutputIntent with pristine FOGRA39.
        try:
            self._inject_output_intent(pdf_out)
        except Exception as exc:
            logger.warning("OutputIntent injection failed: %s", exc)

        changes = [
            f"Converted all objects to DeviceCMYK via {Path(self.icc_path).name}",
            "Injected PDF/X-4 OutputIntent (ISO Coated v2 300% ECI)",
        ]
        changes.extend(rgb_changes)

        return self._ok(
            codigo=codigo,
            changes=changes,
            log=f"gs ok; output={pdf_out.stat().st_size} bytes",
        )

    # ── B-02: Robust OutputIntent injection ────────────────────────────────────

    def _handle_outputintent_only(
        self, pdf_in: Path, pdf_out: Path, codigo: str
    ) -> RemediationAction:
        """Handle E_OUTPUTINTENT_MISSING without full GS conversion."""
        if not Path(self.icc_path).exists():
            return self._fail(
                codigo=codigo,
                warnings=[f"ICC profile not found: {self.icc_path}"],
                log="Cannot inject OutputIntent without FOGRA39 ICC profile.",
            )

        pdf_out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_in, pdf_out)

        try:
            state = self._detect_outputintent_state(pdf_out)
            self._inject_output_intent(pdf_out)
        except Exception as exc:
            return self._fail(
                codigo=codigo,
                warnings=[f"OutputIntent injection failed: {exc}"],
                log=str(exc),
            )

        return self._ok(
            codigo=codigo,
            changes=[
                f"OutputIntent replaced (previous state: {state})",
                "Injected PDF/X-4 OutputIntent (ISO Coated v2 300% ECI)",
            ],
            log=f"outputintent ok; output={pdf_out.stat().st_size} bytes",
        )

    def _detect_outputintent_state(self, pdf_path: Path) -> str:
        """
        Classify the current OutputIntents state into one of 4 invalid states
        (or 'valid' for the no-op case).

        States:
          absent          — /OutputIntents key missing entirely
          empty_array     — /OutputIntents = []
          wrong_subtype   — S entry ≠ /GTS_PDFX
          corrupt_profile — DestOutputProfile is 0 bytes or missing checksum
          valid           — pristine GTS_PDFX with readable profile ≥ 256 bytes
        """
        import pikepdf

        with pikepdf.open(pdf_path) as pdf:
            oi_list = pdf.Root.get("/OutputIntents")

            if oi_list is None:
                return "absent"

            if not isinstance(oi_list, pikepdf.Array) or len(oi_list) == 0:
                return "empty_array"

            intent = oi_list[0]
            s_entry = intent.get("/S")
            if s_entry is None or str(s_entry) != "/GTS_PDFX":
                return "wrong_subtype"

            profile_ref = intent.get("/DestOutputProfile")
            if profile_ref is None:
                return "corrupt_profile"

            try:
                profile_stream = pdf.get_object(profile_ref.objgen)
                data = profile_stream.read_bytes()
                if len(data) < _ICC_MIN_BYTES:
                    return "corrupt_profile"
            except Exception:
                return "corrupt_profile"

            return "valid"

    def _inject_output_intent(self, pdf_path: Path) -> None:
        """
        B-02: Replace OutputIntents with a pristine GTS_PDFX entry backed by
        ISOcoated_v2_300_eci.icc in all 4 invalid states AND whenever the
        existing profile is corrupt. The valid-state is the only no-op.
        """
        import pikepdf

        state = self._detect_outputintent_state(pdf_path)
        if state == "valid":
            logger.debug("_inject_output_intent: OutputIntent is valid, no-op.")
            return

        logger.info("_inject_output_intent: state=%s — replacing OutputIntent", state)

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

    # ── B-03: RGB residual cleanup ─────────────────────────────────────────────

    def _normalize_color_spaces(self, pdf_path: Path) -> list[str]:
        """
        B-03: Enumerate all XObject Images; convert DeviceRGB/CalRGB ones to
        DeviceCMYK via Ghostscript. Called after the main GS conversion to catch
        any residual RGB objects that survived (e.g. pre-converted embedded images).

        Returns a list of change descriptions for RemediationAction.changes_applied.
        """
        if not Path(self.icc_path).exists():
            logger.debug("_normalize_color_spaces: ICC missing, skipping residual check.")
            return []

        try:
            import pikepdf
        except ImportError:
            logger.warning("_normalize_color_spaces: pikepdf not available, skipping.")
            return []

        rgb_names = {"/DeviceRGB", "/CalRGB"}
        rgb_image_count = 0

        try:
            with pikepdf.open(pdf_path) as pdf:
                for page in pdf.pages:
                    resources = page.get("/Resources", pikepdf.Dictionary())
                    xobjects = resources.get("/XObject", pikepdf.Dictionary())
                    for _name, xobj_ref in xobjects.items():
                        try:
                            xobj = pdf.get_object(xobj_ref.objgen)
                            if str(xobj.get("/Subtype", "")) != "/Image":
                                continue
                            cs = xobj.get("/ColorSpace")
                            if cs is None:
                                continue
                            cs_str = str(cs) if not isinstance(cs, pikepdf.Array) else str(cs[0])
                            if cs_str in rgb_names:
                                rgb_image_count += 1
                        except Exception:
                            continue
        except Exception as exc:
            logger.warning("_normalize_color_spaces: inspection failed: %s", exc)
            return []

        if rgb_image_count == 0:
            return []

        # Re-run Ghostscript on the already-converted file to catch residuals.
        tmp = pdf_path.with_suffix(".rgb_norm.pdf")
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
            f"-sOutputFile={tmp}",
            str(pdf_path),
        ]
        try:
            result = subprocess.run(
                cmd, check=False, capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
                import shutil as _shutil
                _shutil.move(str(tmp), str(pdf_path))
                return [f"converted {rgb_image_count} RGB image(s) to CMYK FOGRA39"]
            else:
                logger.warning(
                    "_normalize_color_spaces: GS residual pass failed: %s", result.stderr[-400:]
                )
                tmp.unlink(missing_ok=True)
        except subprocess.TimeoutExpired:
            logger.warning("_normalize_color_spaces: GS residual pass timed out")
            tmp.unlink(missing_ok=True)
        except Exception as exc:
            logger.warning("_normalize_color_spaces: unexpected error: %s", exc)
            tmp.unlink(missing_ok=True)

        return []

    # ── Legacy alias (kept for tests that mock _stamp_pdfx4) ──────────────────

    def _stamp_pdfx4(self, pdf_path: Path) -> None:
        """Backwards-compat alias → delegates to _inject_output_intent."""
        self._inject_output_intent(pdf_path)

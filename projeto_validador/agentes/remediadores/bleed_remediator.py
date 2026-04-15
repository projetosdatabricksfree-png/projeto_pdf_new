"""
BleedRemediator — generate print bleed via mirror-edge technique.

Strategy:
1. Render page to 300 DPI pixmap via PyMuPDF.
2. Extend the raster by 3mm on each side using pyvips `embed` with mirror mode.
3. Reconstruct a PDF page with expanded MediaBox; original dims become TrimBox.
4. Fallback: if critical content (text/vectors) exists within the 3mm border zone,
   apply scale-to-bleed 102% instead, emitting a quality_loss_warning.

Handles:
  - G002 : TrimBox == MediaBox (no bleed present)
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from app.api.schemas import RemediationAction, ValidationResult

from .base import BaseRemediator

logger = logging.getLogger(__name__)

BLEED_MM = 3.0
RENDER_DPI = 300
MM_TO_PT = 72.0 / 25.4
BLEED_PT = BLEED_MM * MM_TO_PT  # ≈ 8.504 pt


class BleedRemediator(BaseRemediator):
    name = "BleedRemediator"
    handles = ("G002",)

    def remediate(
        self,
        pdf_in: Path,
        pdf_out: Path,
        validation_result: ValidationResult,
    ) -> RemediationAction:
        try:
            import pymupdf  # noqa: PLC0415
        except ImportError:
            return self._fail(
                codigo=validation_result.codigo or "G002",
                warnings=["PyMuPDF (pymupdf) not installed"],
                log="BleedRemediator requires pymupdf.",
            )
        try:
            import pyvips  # noqa: PLC0415
        except ImportError:
            return self._fail(
                codigo=validation_result.codigo or "G002",
                warnings=["pyvips not installed"],
                log="BleedRemediator requires pyvips for mirror-edge compositing.",
            )

        codigo = validation_result.codigo or "G002"
        pdf_out.parent.mkdir(parents=True, exist_ok=True)

        try:
            doc = pymupdf.open(str(pdf_in))
        except Exception as exc:
            return self._fail(
                codigo=codigo,
                warnings=[f"Failed to open PDF: {exc}"],
                log=str(exc),
            )

        try:
            new_doc = pymupdf.open()
            warnings_collected: list[str] = []
            changes_collected: list[str] = []

            for page_index, page in enumerate(doc):
                orig_rect = page.rect  # original MediaBox (= TrimBox for no-bleed files)
                orig_w_pt = orig_rect.width
                orig_h_pt = orig_rect.height

                has_border_content = self._has_border_content(page, BLEED_PT)

                if has_border_content:
                    result_page, w_str = self._scale_to_bleed_page(
                        new_doc, page, orig_rect, pyvips
                    )
                    warnings_collected.append(
                        f"page {page_index + 1}: mirror-edge inviável: texto na borda; "
                        "aplicado scale-to-bleed 102%"
                    )
                    changes_collected.append(f"page {page_index + 1}: scale-to-bleed 102%")
                    logger.warning(
                        "BleedRemediator page %d: border content detected, scale-to-bleed fallback",
                        page_index + 1,
                    )
                else:
                    result_page = self._mirror_edge_page(
                        new_doc, page, orig_rect, orig_w_pt, orig_h_pt, pyvips, pymupdf
                    )
                    changes_collected.append(
                        f"page {page_index + 1}: mirror-edge 3mm bleed added"
                    )

            doc.close()
            new_doc.save(str(pdf_out))
            new_doc.close()

        except Exception as exc:
            logger.exception("BleedRemediator failed: %s", exc)
            return self._fail(
                codigo=codigo,
                warnings=[f"Unexpected error during bleed remediation: {exc}"],
                log=str(exc),
            )

        if not pdf_out.exists() or pdf_out.stat().st_size == 0:
            return self._fail(
                codigo=codigo,
                warnings=["Output PDF not produced or empty"],
                log="BleedRemediator produced no output.",
            )

        if warnings_collected:
            return self._warn(
                codigo=codigo,
                changes=changes_collected,
                warnings=warnings_collected,
                log=f"output={pdf_out.stat().st_size} bytes; fallback used on some pages",
                severity="low",
            )

        return self._ok(
            codigo=codigo,
            changes=changes_collected,
            log=f"mirror-edge ok; output={pdf_out.stat().st_size} bytes",
        )

    # ── Private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _has_border_content(page, bleed_pt: float) -> bool:
        """Return True if text or vector content exists within the 3mm border zone."""
        rect = page.rect
        border_rects = [
            # top strip
            (rect.x0, rect.y0, rect.x1, rect.y0 + bleed_pt),
            # bottom strip
            (rect.x0, rect.y1 - bleed_pt, rect.x1, rect.y1),
            # left strip
            (rect.x0, rect.y0, rect.x0 + bleed_pt, rect.y1),
            # right strip
            (rect.x1 - bleed_pt, rect.y0, rect.x1, rect.y1),
        ]
        import pymupdf  # noqa: PLC0415

        for x0, y0, x1, y1 in border_rects:
            clip = pymupdf.Rect(x0, y0, x1, y1)
            blocks = page.get_text("blocks", clip=clip)
            if blocks:
                return True
            # Also check for vector drawings (paths)
            paths = page.get_drawings()
            for path in paths:
                path_rect = pymupdf.Rect(path["rect"])
                if clip.intersects(path_rect):
                    return True
        return False

    @staticmethod
    def _mirror_edge_page(new_doc, page, orig_rect, orig_w_pt, orig_h_pt, pyvips, pymupdf):
        """Render page, mirror-extend 3mm, insert into new_doc. Returns new page."""
        mat = pymupdf.Matrix(RENDER_DPI / 72, RENDER_DPI / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        bleed_px = int(round(BLEED_PT * RENDER_DPI / 72))
        new_w_px = pix.width + 2 * bleed_px
        new_h_px = pix.height + 2 * bleed_px

        # Build pyvips image from PyMuPDF samples
        vips_img = pyvips.Image.new_from_memory(
            pix.samples, pix.width, pix.height, pix.n, "uchar"
        )

        # embed with mirror extension — pyvips fills the border by mirroring edge pixels
        extended = vips_img.embed(bleed_px, bleed_px, new_w_px, new_h_px, extend="mirror")

        new_w_pt = orig_w_pt + 2 * BLEED_PT
        new_h_pt = orig_h_pt + 2 * BLEED_PT

        new_page = new_doc.new_page(width=new_w_pt, height=new_h_pt)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            extended.write_to_file(tmp_path)
            new_page.insert_image(new_page.rect, filename=tmp_path)
        finally:
            import os  # noqa: PLC0415

            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        # Set TrimBox = original page dimensions, centered in the new MediaBox
        trim = pymupdf.Rect(BLEED_PT, BLEED_PT, BLEED_PT + orig_w_pt, BLEED_PT + orig_h_pt)
        new_page.set_trimbox(trim)

        return new_page

    @staticmethod
    def _scale_to_bleed_page(new_doc, page, orig_rect, pyvips):
        """Fallback: scale content 102% to fill bleed zone. Returns new page."""
        import pymupdf  # noqa: PLC0415

        SCALE = 1.02
        orig_w_pt = orig_rect.width
        orig_h_pt = orig_rect.height

        # Render at full scale
        mat = pymupdf.Matrix(RENDER_DPI / 72, RENDER_DPI / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        vips_img = pyvips.Image.new_from_memory(
            pix.samples, pix.width, pix.height, pix.n, "uchar"
        )

        scaled_w = int(round(pix.width * SCALE))
        scaled_h = int(round(pix.height * SCALE))
        scaled = vips_img.resize(SCALE)

        # Crop/embed to maintain original canvas size + bleed border
        bleed_px = int(round(BLEED_PT * RENDER_DPI / 72))
        new_w_px = pix.width + 2 * bleed_px
        new_h_px = pix.height + 2 * bleed_px
        offset_x = (new_w_px - scaled_w) // 2
        offset_y = (new_h_px - scaled_h) // 2
        final = scaled.embed(
            offset_x, offset_y, new_w_px, new_h_px, extend="black"
        )

        new_w_pt = orig_w_pt + 2 * BLEED_PT
        new_h_pt = orig_h_pt + 2 * BLEED_PT
        new_page = new_doc.new_page(width=new_w_pt, height=new_h_pt)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            final.write_to_file(tmp_path)
            new_page.insert_image(new_page.rect, filename=tmp_path)
        finally:
            import os  # noqa: PLC0415

            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        trim = pymupdf.Rect(BLEED_PT, BLEED_PT, BLEED_PT + orig_w_pt, BLEED_PT + orig_h_pt)
        new_page.set_trimbox(trim)

        return new_page, f"scale-to-bleed 102% ({orig_w_pt:.1f}×{orig_h_pt:.1f}pt)"

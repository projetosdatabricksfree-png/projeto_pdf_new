"""
BleedRemediator unit tests — A-02 AC6.

Synthetic 100×100mm PDF (no bleed) must exit as 106×106mm with
TrimBox = 100×100mm centred at offset (8.504pt, 8.504pt).
"""
from __future__ import annotations

import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentes.remediadores.bleed_remediator import BLEED_PT, BleedRemediator
from app.api.schemas import ValidationResult

MM_TO_PT = 72.0 / 25.4


def _make_synthetic_pdf(path: Path, width_mm: float = 100.0, height_mm: float = 100.0) -> Path:
    """Create a minimal PDF with the given dimensions in mm, no bleed."""
    try:
        import pymupdf
    except ImportError:
        pytest.skip("pymupdf not installed")

    w_pt = width_mm * MM_TO_PT
    h_pt = height_mm * MM_TO_PT
    doc = pymupdf.open()
    doc.new_page(width=w_pt, height=h_pt)
    doc.save(str(path))
    doc.close()
    return path


def _get_page_boxes(path: Path) -> tuple[tuple, tuple | None]:
    """Return (mediabox_rect, trimbox_rect_or_None) for page 0."""
    import pymupdf

    with pymupdf.open(str(path)) as doc:
        page = doc[0]
        media = page.mediabox
        try:
            trim = page.trimbox
        except Exception:
            trim = None
        return media, trim


# ── Tests ────────────────────────────────────────────────────────────────────

class TestBleedRemediatorMissingLibs:
    def test_fails_gracefully_without_pymupdf(self, tmp_path):
        vr = ValidationResult(status="REPROVADO", codigo="G002")
        with patch.dict("sys.modules", {"pymupdf": None}):
            action = BleedRemediator().remediate(
                tmp_path / "in.pdf", tmp_path / "out.pdf", vr
            )
        assert action.success is False
        assert "PyMuPDF" in action.quality_loss_warnings[0]

    def test_fails_gracefully_without_pyvips(self, tmp_path):
        vr = ValidationResult(status="REPROVADO", codigo="G002")
        with patch.dict("sys.modules", {"pyvips": None}):
            action = BleedRemediator().remediate(
                tmp_path / "in.pdf", tmp_path / "out.pdf", vr
            )
        assert action.success is False

    def test_fails_gracefully_on_invalid_pdf(self, tmp_path):
        bad_pdf = tmp_path / "bad.pdf"
        bad_pdf.write_bytes(b"not a pdf")
        vr = ValidationResult(status="REPROVADO", codigo="G002")
        action = BleedRemediator().remediate(bad_pdf, tmp_path / "out.pdf", vr)
        assert action.success is False


class TestBleedRemediatorGeometry:
    """Integration test — requires pymupdf + pyvips installed in the environment."""

    @pytest.fixture
    def synthetic_pdf(self, tmp_path) -> Path:
        return _make_synthetic_pdf(tmp_path / "no_bleed.pdf", 100, 100)

    def test_mediabox_expands_by_bleed(self, tmp_path, synthetic_pdf):
        """A-02 AC6: 100×100mm PDF → 106×106mm MediaBox after bleed."""
        pytest.importorskip("pymupdf")
        pytest.importorskip("pyvips")

        vr = ValidationResult(status="REPROVADO", codigo="G002")
        out = tmp_path / "with_bleed.pdf"
        action = BleedRemediator().remediate(synthetic_pdf, out, vr)

        assert action.success is True, f"Expected success; got: {action}"
        assert out.exists() and out.stat().st_size > 0

        media, trim = _get_page_boxes(out)

        orig_w_pt = 100.0 * MM_TO_PT
        orig_h_pt = 100.0 * MM_TO_PT
        expected_w = orig_w_pt + 2 * BLEED_PT
        expected_h = orig_h_pt + 2 * BLEED_PT

        assert math.isclose(media.width, expected_w, abs_tol=1.0), (
            f"MediaBox width: expected ≈{expected_w:.2f}pt, got {media.width:.2f}pt"
        )
        assert math.isclose(media.height, expected_h, abs_tol=1.0), (
            f"MediaBox height: expected ≈{expected_h:.2f}pt, got {media.height:.2f}pt"
        )

    def test_trimbox_is_original_dimensions_centred(self, tmp_path, synthetic_pdf):
        """TrimBox must equal the original 100×100mm, offset by BLEED_PT."""
        pytest.importorskip("pymupdf")
        pytest.importorskip("pyvips")

        vr = ValidationResult(status="REPROVADO", codigo="G002")
        out = tmp_path / "with_bleed.pdf"
        BleedRemediator().remediate(synthetic_pdf, out, vr)

        media, trim = _get_page_boxes(out)

        assert trim is not None, "TrimBox must be set on the output PDF"

        orig_w_pt = 100.0 * MM_TO_PT
        orig_h_pt = 100.0 * MM_TO_PT

        assert math.isclose(trim.x0, BLEED_PT, abs_tol=1.0)
        assert math.isclose(trim.y0, BLEED_PT, abs_tol=1.0)
        assert math.isclose(trim.width, orig_w_pt, abs_tol=1.0)
        assert math.isclose(trim.height, orig_h_pt, abs_tol=1.0)

    def test_no_quality_loss_warnings_on_clean_page(self, tmp_path, synthetic_pdf):
        """A blank/empty page produces no quality_loss_warnings (no border content)."""
        pytest.importorskip("pymupdf")
        pytest.importorskip("pyvips")

        vr = ValidationResult(status="REPROVADO", codigo="G002")
        out = tmp_path / "with_bleed.pdf"
        action = BleedRemediator().remediate(synthetic_pdf, out, vr)

        assert action.success is True
        assert not action.quality_loss_warnings

    def test_action_codigo_matches_input(self, tmp_path, synthetic_pdf):
        pytest.importorskip("pymupdf")
        pytest.importorskip("pyvips")

        vr = ValidationResult(status="REPROVADO", codigo="G002")
        out = tmp_path / "with_bleed.pdf"
        action = BleedRemediator().remediate(synthetic_pdf, out, vr)
        assert action.codigo == "G002"
        assert action.remediator == "BleedRemediator"

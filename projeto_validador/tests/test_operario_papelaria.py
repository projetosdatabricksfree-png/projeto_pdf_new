"""
Tests for the Papelaria Plana operário.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestDimensionChecker:
    """Tests for dimension validation."""

    @pytest.fixture
    def create_pdf(self, tmp_path):
        """Helper to create a test PDF with specific dimensions."""
        def _create(width_pt, height_pt):
            try:
                import fitz
                doc = fitz.open()
                doc.new_page(width=width_pt, height=height_pt)
                path = str(tmp_path / "test.pdf")
                doc.save(path)
                doc.close()
                return path
            except ImportError:
                pytest.skip("PyMuPDF not installed")
        return _create

    def test_iso7810_id1_approved(self, create_pdf):
        """ISO 7810 ID-1 card dimensions should be approved."""
        from agentes.operarios.operario_papelaria_plana.tools.dimension_checker import check_dimensions

        # 85.60mm × 53.98mm in points (1mm = 72/25.4 pt)
        width_pt = 85.60 * 72 / 25.4
        height_pt = 53.98 * 72 / 25.4
        path = create_pdf(width_pt, height_pt)

        result = check_dimensions(path)
        assert result["status"] == "OK"
        assert "ISO 7810" in result.get("norma", "")

    def test_european_format_approved(self, create_pdf):
        """European card dimensions should be approved."""
        from agentes.operarios.operario_papelaria_plana.tools.dimension_checker import check_dimensions

        width_pt = 85.00 * 72 / 25.4
        height_pt = 55.00 * 72 / 25.4
        path = create_pdf(width_pt, height_pt)

        result = check_dimensions(path)
        assert result["status"] == "OK"
        assert "Europeu" in result.get("norma", "")

    def test_nonstandard_dimension_rejected(self, create_pdf):
        """Non-standard dimensions should trigger E001."""
        from agentes.operarios.operario_papelaria_plana.tools.dimension_checker import check_dimensions

        width_pt = 100 * 72 / 25.4
        height_pt = 100 * 72 / 25.4
        path = create_pdf(width_pt, height_pt)

        result = check_dimensions(path)
        assert result["status"] == "ERRO"
        assert result["codigo"] == "E001_DIMENSION_MISMATCH"


class TestBleedChecker:
    """Tests for bleed validation."""

    @pytest.fixture
    def create_pdf_with_bleed(self, tmp_path):
        """Helper to create PDF with specific bleed."""
        def _create(bleed_mm=0):
            try:
                import fitz
                doc = fitz.open()
                # Card dimensions in points
                trim_w = 85.60 * 72 / 25.4
                trim_h = 53.98 * 72 / 25.4
                bleed_pt = bleed_mm * 72 / 25.4

                page = doc.new_page(
                    width=trim_w + 2 * bleed_pt,
                    height=trim_h + 2 * bleed_pt,
                )
                # Set trim box (inner area without bleed)
                page.set_trimbox(fitz.Rect(
                    bleed_pt, bleed_pt,
                    trim_w + bleed_pt, trim_h + bleed_pt,
                ))
                path = str(tmp_path / "test_bleed.pdf")
                doc.save(path)
                doc.close()
                return path
            except ImportError:
                pytest.skip("PyMuPDF not installed")
        return _create

    def test_no_bleed_rejected(self, create_pdf_with_bleed):
        """Zero bleed should trigger E002_MISSING_BLEED."""
        from agentes.operarios.operario_papelaria_plana.tools.bleed_checker import check_bleed

        path = create_pdf_with_bleed(bleed_mm=0)
        result = check_bleed(path)
        assert result["status"] == "ERRO"
        assert "E002" in result.get("codigo", "") or "E003" in result.get("codigo", "")

    def test_valid_bleed_approved(self, create_pdf_with_bleed):
        """2.5mm bleed should be approved."""
        from agentes.operarios.operario_papelaria_plana.tools.bleed_checker import check_bleed

        path = create_pdf_with_bleed(bleed_mm=2.5)
        result = check_bleed(path)
        assert result["status"] == "OK"


class TestFontChecker:
    """Tests for font embedding checker."""

    @pytest.fixture
    def create_pdf_with_text(self, tmp_path):
        """Create a PDF with embedded text."""
        def _create():
            try:
                import fitz
                doc = fitz.open()
                page = doc.new_page()
                page.insert_text((72, 72), "Hello World", fontsize=12)
                path = str(tmp_path / "test_fonts.pdf")
                doc.save(path)
                doc.close()
                return path
            except ImportError:
                pytest.skip("PyMuPDF not installed")
        return _create

    def test_embedded_fonts_approved(self, create_pdf_with_text):
        """PDF with embedded fonts should be approved."""
        from agentes.operarios.operario_papelaria_plana.tools.font_checker import check_fonts_embedded

        path = create_pdf_with_text()
        result = check_fonts_embedded(path)
        assert result["status"] == "OK"

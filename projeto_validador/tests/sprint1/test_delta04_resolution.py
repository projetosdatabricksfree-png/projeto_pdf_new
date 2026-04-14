"""
Regression tests for Sprint 1: DELTA-04 / DELTA-05 — Dual-Tier Image Resolution.

Validates:
- IM-01 / IM-07: Effective DPI via CTM, dual-tier Error/Warning
- §4.26 exception: images ≤ 16px skipped
- Profile injection works end-to-end (regression guard for run_full_suite bug)
"""
import sys
import fitz
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentes.operarios.shared_tools.gwg.compression_checker import check_compression
from agentes.operarios.shared_tools.gwg.profile_matcher import get_gwg_profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf_with_images(tmp_path, images: list[tuple[int, int, float]]) -> str:
    """
    Creates a synthetic PDF with raster images at specified effective DPI.

    Args:
        images: list of (width_px, height_px, target_dpi)
    """
    doc = fitz.open()
    page = doc.new_page()

    for w_px, h_px, target_dpi in images:
        # bbox size in points so that effective DPI = target_dpi
        bbox_pts = w_px / (target_dpi / 72.0)
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, w_px, h_px), False)
        page.insert_image(fitz.Rect(10, 10, 10 + bbox_pts, 10 + bbox_pts), pixmap=pix)

    pdf_path = str(tmp_path / "test_res.pdf")
    doc.save(pdf_path)
    doc.close()
    return pdf_path


# ---------------------------------------------------------------------------
# AC1 — Magazine 148 DPI → ERRO (< 149 threshold)
# ---------------------------------------------------------------------------

def test_delta04_magazine_critical_error(tmp_path):
    """AC1: Image at 148 DPI must generate ERRO for MagazineAds profile."""
    profile = get_gwg_profile("MagazineAds_CMYK")
    assert profile["min_image_resolution"] == 149, "Profile threshold sanity check"

    pdf = _make_pdf_with_images(tmp_path, [(100, 100, 148.0)])
    result = check_compression(pdf, profile)

    assert result["status"] == "ERRO", f"Expected ERRO, got: {result}"
    codes = [i["codigo"] for i in result.get("issues", [])]
    assert "E_LOW_RESOLUTION_CRITICAL" in codes, f"Missing critical code. Issues: {codes}"


# ---------------------------------------------------------------------------
# AC2 — Magazine 200 DPI → AVISO (between 149 and 224)
# ---------------------------------------------------------------------------

def test_delta04_magazine_marginal_warning(tmp_path):
    """AC2: Image at 200 DPI must generate AVISO for MagazineAds profile."""
    profile = get_gwg_profile("MagazineAds_CMYK")
    assert profile["warn_image_resolution"] == 224, "Profile warn threshold sanity check"

    pdf = _make_pdf_with_images(tmp_path, [(100, 100, 200.0)])
    result = check_compression(pdf, profile)

    assert result["status"] == "AVISO", f"Expected AVISO, got: {result}"
    codes = [i["codigo"] for i in result.get("issues", [])]
    assert "W_LOW_RESOLUTION_MARGINAL" in codes, f"Missing warning code. Issues: {codes}"


# ---------------------------------------------------------------------------
# AC3 — Magazine 230 DPI → OK (above 224 warn threshold)
# ---------------------------------------------------------------------------

def test_delta04_magazine_ok(tmp_path):
    """AC3: Image at 230 DPI must pass with status OK for MagazineAds profile."""
    profile = get_gwg_profile("MagazineAds_CMYK")

    pdf = _make_pdf_with_images(tmp_path, [(100, 100, 230.0)])
    result = check_compression(pdf, profile)

    # Only resolution-related codes should be absent
    res_codes = {"E_LOW_RESOLUTION_CRITICAL", "W_LOW_RESOLUTION_MARGINAL"}
    actual_codes = {i["codigo"] for i in result.get("issues", [])}
    assert res_codes.isdisjoint(actual_codes), f"Unexpected resolution issues: {actual_codes}"


# ---------------------------------------------------------------------------
# AC4 — 16px exception (§4.26): tiny image must be skipped
# ---------------------------------------------------------------------------

def test_delta04_16px_exception_skipped(tmp_path):
    """AC4: Image with dimension ≤ 16px must be skipped even at 50 DPI."""
    profile = get_gwg_profile("MagazineAds_CMYK")

    # 10x10px at 50 DPI → would be an error if not skipped
    pdf = _make_pdf_with_images(tmp_path, [(10, 10, 50.0)])
    result = check_compression(pdf, profile)

    res_codes = {"E_LOW_RESOLUTION_CRITICAL", "W_LOW_RESOLUTION_MARGINAL"}
    actual_codes = {i["codigo"] for i in result.get("issues", [])}
    assert res_codes.isdisjoint(actual_codes), f"16px image should be skipped. Issues: {actual_codes}"


# ---------------------------------------------------------------------------
# DELTA-05 — Newspaper profile has different thresholds (99/149)
# ---------------------------------------------------------------------------

def test_delta05_newspaper_thresholds(tmp_path):
    """DELTA-05: Newspaper profile uses 99 (err) / 149 (warn) — distinct from Magazine."""
    profile = get_gwg_profile("NewspaperAds_CMYK")
    assert profile["min_image_resolution"] == 99
    assert profile["warn_image_resolution"] == 149

    # 120 DPI → above 99 err, but below 149 warn → should be AVISO
    pdf = _make_pdf_with_images(tmp_path, [(100, 100, 120.0)])
    result = check_compression(pdf, profile)

    assert result["status"] == "AVISO", f"Expected AVISO for 120dpi on Newspaper, got: {result}"
    codes = [i["codigo"] for i in result.get("issues", [])]
    assert "W_LOW_RESOLUTION_MARGINAL" in codes


# ---------------------------------------------------------------------------
# Regression: profile must be forwarded through run_full_suite._run_compression
# ---------------------------------------------------------------------------

def test_delta04_profile_forwarded_regression(tmp_path):
    """
    Regression guard: _run_compression in run_full_suite must forward profile.

    Newspaper err threshold (99 DPI) is below Magazine default (150 DPI).
    A 120 DPI image should be OK under Newspaper but ERRO under Magazine default.
    If profile is NOT forwarded, result would be ERRO regardless of profile — caught here.
    """
    from agentes.operarios.shared_tools.gwg.run_full_suite import _run_compression

    newspaper_profile = get_gwg_profile("NewspaperAds_CMYK")
    pdf = _make_pdf_with_images(tmp_path, [(100, 100, 120.0)])

    result = _run_compression(pdf, newspaper_profile)

    # Under Newspaper (err=99), 120 DPI should not be E_LOW_RESOLUTION_CRITICAL
    assert result["status"] != "ERRO" or "E_LOW_RESOLUTION_CRITICAL" not in [
        i["codigo"] for i in result.get("issues", [])
    ], (
        "Profile not forwarded: 120 DPI flagged as CRITICAL despite Newspaper err=99. "
        f"Got: {result}"
    )

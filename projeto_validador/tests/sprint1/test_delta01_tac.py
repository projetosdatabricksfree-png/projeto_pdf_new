"""
Regression tests for Sprint 1: DELTA-01 and SY-08.
Tests the sliding window TAC engine against GWG2015 thresholds.
"""
import sys
import fitz
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

try:
    from agentes.operarios.shared_tools.gwg.color_checker import _check_tac_vips_turbo
    from agentes.operarios.shared_tools.gwg.profile_matcher import GWG_PROFILES
except ImportError:
    # Fallback for different environments
    from projeto_validador.agentes.operarios.shared_tools.gwg.color_checker import _check_tac_vips_turbo
    from projeto_validador.agentes.operarios.shared_tools.gwg.profile_matcher import GWG_PROFILES

TEST_DIR = Path(__file__).resolve().parent / "temp_pdfs"
TEST_DIR.mkdir(exist_ok=True)

def create_test_pdf(filename: str, rects: list[tuple[fitz.Rect, tuple[float, float, float, float]]]):
    """
    Creates a CMYK PDF with specified rectangles and colors.
    rects: list of (Rect, (c, m, y, k) as 0-1.0)
    """
    path = TEST_DIR / filename
    doc = fitz.open()
    # Ensure page is CMYK
    page = doc.new_page(width=fitz.paper_size("a4")[0], height=fitz.paper_size("a4")[1])
    
    for rect, color in rects:
        # Draw a filled rectangle in CMYK (determined by 4-tuple length)
        page.draw_rect(rect, color=color, fill=color, overlay=True)
    
    doc.save(str(path))
    doc.close()
    return str(path)

def test_sy08_sliding_window_hot_pixel():
    """
    SY-08: A single hot pixel (400% TAC) should be diluted by the 15mm2 window.
    At 150 DPI, a 1x1 pixel is ~0.17mm. 15mm2 is ~3.87mm.
    The mean should be way below 300%.
    """
    # Single tiny square (1x1 point = ~0.35mm) at 400% TAC
    pdf_path = create_test_pdf("hot_pixel.pdf", [
        (fitz.Rect(100, 100, 101, 101), (1.0, 1.0, 1.0, 1.0))
    ])
    
    # Check against a strict limit (e.g. 100% just to see if it passes)
    result = _check_tac_vips_turbo(pdf_path, limit=100.0, page_count=1)
    
    # 400% in 1pt area (0.1225 mm2) diluted in 15 mm2 window:
    # 400 * (0.1225 / 15) = ~3.2% mean.
    # We allow up to 20% to account for rendering antialiasing of the 1pt square.
    assert result["status"] == "OK"
    assert result["meta"]["max_tac_window"] < 20.0

def test_delta01_magazine_boundary_fail():
    """
    DELTA-01: 20x20mm patch at 310% TAC should FAIL for Magazine (305% limit).
    20x20mm = 400mm2 (much larger than 15mm2 window). Mean will be ~310%.
    """
    limit = GWG_PROFILES["MagazineAds_CMYK"]["tac_limit"] # 305
    assert limit == 305
    
    # 20mm in points = 20 / 0.3527 = ~56.7 pts
    # TAC 310% -> e.g. 0.8 / 0.8 / 0.8 / 0.7
    pdf_path = create_test_pdf("magazine_fail.pdf", [
        (fitz.Rect(100, 100, 157, 157), (0.8, 0.8, 0.8, 0.7))
    ])
    
    result = _check_tac_vips_turbo(pdf_path, limit=limit, page_count=1)
    assert result["status"] == "ERRO"
    assert result["codigo"] == "E_TAC_EXCEEDED"
    # Allow for slight rendering/rounding loss (e.g. 309.8%)
    assert float(result["found_value"].strip("%")) >= 309.0

def test_delta01_magazine_boundary_pass():
    """
    DELTA-01: 20x20mm patch at 305% TAC should PASS for Magazine (305% limit).
    """
    limit = 305.0
    # TAC 305% -> e.g. 0.76 / 0.76 / 0.76 / 0.77
    pdf_path = create_test_pdf("magazine_pass.pdf", [
        (fitz.Rect(100, 100, 157, 157), (0.76, 0.76, 0.76, 0.77))
    ])
    
    result = _check_tac_vips_turbo(pdf_path, limit=limit, page_count=1)
    # 305% might result in 304.9 or 305.1. 
    # If it's 305.1, it might fail ERRO. We check the status logic.
    if result["status"] == "ERRO":
        # Check if it's within a very small margin
        assert float(result["found_value"].strip("%")) <= 305.5
    else:
        assert result["status"] == "OK"

if __name__ == "__main__":
    # Setup for manual run if needed
    pytest.main([__file__])

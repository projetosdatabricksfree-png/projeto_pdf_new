import fitz
import os
import sys

# Add project root to path
sys.path.append(os.getcwd() + "/projeto_validador")

from agentes.operarios.shared_tools.gwg.compression_checker import check_compression
from agentes.operarios.shared_tools.gwg.profile_matcher import get_gwg_profile

def create_test_pdf(filename):
    doc = fitz.open()
    page = doc.new_page()
    
    # Instance 1: 148 DPI
    # points = pixels / (dpi / 72) -> 100 / (148 / 72) = 48.6 points
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 100), False)
    page.insert_image(fitz.Rect(10, 10, 10 + 48.6, 10 + 48.6), pixmap=pix)
    
    # Instance 2: 200 DPI
    # 100 / (200 / 72) = 36.0 points
    page.insert_image(fitz.Rect(100, 10, 100 + 36, 10 + 36), pixmap=pix)
    
    # Instance 3: 10px image (should be skipped)
    pix_small = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10), False)
    page.insert_image(fitz.Rect(200, 10, 210, 20), pixmap=pix_small)
    
    doc.save(filename)
    doc.close()

def test_resolution():
    test_file = "projeto_validador/scratch/resolution_test.pdf"
    create_test_pdf(test_file)
    
    profile = get_gwg_profile("MagazineAds_CMYK")
    print(f"Testing Profile: {profile['name']}")
    print(f"Err: <{profile['min_image_resolution']}, Warn: <{profile['warn_image_resolution']}")
    
    results = check_compression(test_file, profile)
    
    print(f"\nStatus: {results['status']}")
    print(f"Imagens inspecionadas: {results['images_inspected']}")
    
    for issue in results.get("issues", []):
        text = f"[{issue['severity']}] {issue['codigo']} - Page {issue['page']}: {issue.get('found_value')} (Expected {issue.get('expected_value')})"
        if issue.get('meta'):
            text += f" Dim: {issue['meta']['dim']}"
        print(text)

if __name__ == "__main__":
    test_resolution()

import fitz  # PyMuPDF
import os

BASE_DIR = "/home/diego/Downloads/graphic_pro_validation"

def create_base_pdf(filename, width_mm=100, height_mm=100, bleed_mm=3):
    # Convert mm to points (1mm = 2.83465 pts)
    pts = 2.83465
    w_pts = width_mm * pts
    h_pts = height_mm * pts
    b_pts = bleed_mm * pts

    doc = fitz.open()
    # MediaBox includes bleed
    mediabox = fitz.Rect(0, 0, w_pts + 2*b_pts, h_pts + 2*b_pts)
    page = doc.new_page(width=mediabox.width, height=mediabox.height)
    
    # TrimBox is the final size
    trimbox = fitz.Rect(b_pts, b_pts, b_pts + w_pts, b_pts + h_pts)
    page.set_trimbox(trimbox)
    
    return doc, page, trimbox

def gen_ok_perfect():
    doc, page, trim = create_base_pdf("ok_perfect.pdf")
    # Draw something in CMYK (approximation in PyMuPDF is via colorspace)
    # Note: PyMuPDF uses RGB by default in insert_text/draw_rect unless specified
    page.draw_rect(trim, color=None, fill=(0, 0, 1), overlay=True) # Blue (RGB for now, but we can try to force CMYK if needed)
    # To truly test CMYK, we'd need a CMYK pixmap or colorspace
    page.insert_text((50, 50), "OK Perfect PDF", fontsize=20, color=(0, 0, 0)) # Black
    doc.save(os.path.join(BASE_DIR, "ok_perfect.pdf"))
    doc.close()

def gen_err_missing_bleed():
    # TrimBox == MediaBox (usuellement definido como a mesma área)
    pts = 2.83465
    w, h = 100 * pts, 100 * pts
    doc = fitz.open()
    page = doc.new_page(width=w, height=h)
    # Define MediaBox explicitamente
    page.set_mediabox(fitz.Rect(0, 0, w, h))
    # Para evitar o erro "TrimBox not in MediaBox", usamos a rect da página
    page.set_trimbox(page.rect) 
    page.insert_text((10, 20), "Error: Missing Bleed", color=(1, 0, 0))
    doc.save(os.path.join(BASE_DIR, "err_missing_bleed.pdf"))
    doc.close()

def gen_err_rgb_colorspace():
    doc, page, trim = create_base_pdf("err_rgb_colorspace.pdf")
    # Explicitly draw something in RGB
    page.draw_rect(fitz.Rect(20, 20, 80, 80), color=(1, 0, 0), fill=(1, 0, 0)) # Pure RGB Red
    page.insert_text((20, 100), "Error: RGB Colorspace", color=(0, 0, 0))
    doc.save(os.path.join(BASE_DIR, "err_rgb_colorspace.pdf"))
    doc.close()

def gen_err_low_res():
    doc, page, trim = create_base_pdf("err_low_res.pdf")
    # Create a tiny 10x10 pixmap and scale it up to 100x100 points
    pix = fitz.Pixmap(fitz.csRGB, (0, 0, 10, 10))
    pix.clear_with(255) # White background
    # Add a red dot
    pix.set_pixel(5, 5, (255, 0, 0))
    
    img_rect = fitz.Rect(50, 50, 150, 150)
    page.insert_image(img_rect, pixmap=pix) # This will be very low DPI in print scale
    page.insert_text((50, 40), "Error: Low Resolution (pixelated)", color=(0, 0, 0))
    doc.save(os.path.join(BASE_DIR, "err_low_res.pdf"))
    doc.close()

def gen_err_transparency():
    doc, page, trim = create_base_pdf("err_transparency.pdf")
    # Draw a rectangle with alpha < 1.0 (requires ExtGState in PDF)
    # In PyMuPDF, draw_rect with fill_opacity works
    page.draw_rect(fitz.Rect(30, 30, 120, 120), fill=(0, 1, 0), fill_opacity=0.5)
    page.insert_text((30, 25), "Error: Transparency Active", color=(0, 0, 0))
    doc.save(os.path.join(BASE_DIR, "err_transparency.pdf"))
    doc.close()

if __name__ == "__main__":
    print(f"Generating test PDFs in {BASE_DIR}...")
    gen_ok_perfect()
    gen_err_missing_bleed()
    gen_err_rgb_colorspace()
    gen_err_low_res()
    gen_err_transparency()
    print("Done.")

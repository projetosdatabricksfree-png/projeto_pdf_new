import requests
import time
import os
import fitz  # PyMuPDF
from pathlib import Path
import json

# Configuration
API_BASE = "http://localhost:8001/api/v1"
TEST_FOLDER = Path("/home/diego/Documents/ARQUIVOS_TESTE")
CORRECTED_FOLDER = Path("/home/diego/Documents/Corrigidos")
REPORT_FOLDER = Path("/home/diego/Documents/RELATORIO")
REPORT_FILE = REPORT_FOLDER / "RELATORIO_FINAL.md"

# Ensure folders exist
for folder in [TEST_FOLDER, CORRECTED_FOLDER, REPORT_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

# ─── PDF Generation Logic ───────────────────────────────────────────────────

def create_base_pdf(filename, width_mm=210, height_mm=297, bleed_mm=5, margin_mm=5):
    """Create a standard A4 PDF with 5mm bleed and explicit ArtBox (Safe Zone)."""
    pts = 2.83465
    w_pts = width_mm * pts
    h_pts = height_mm * pts
    b_pts = bleed_mm * pts
    m_pts = margin_mm * pts

    doc = fitz.open()
    # Mediabox includes bleed
    full_w = w_pts + 2*b_pts
    full_h = h_pts + 2*b_pts
    page = doc.new_page(width=full_w, height=full_h)
    
    # Page Boxes
    # trimbox is centered
    trimbox = fitz.Rect(b_pts, b_pts, b_pts + w_pts, b_pts + h_pts)
    page.set_trimbox(trimbox)
    
    # ArtBox: The safe zone (TrimBox minus internal margin)
    artbox = fitz.Rect(trimbox.x0 + m_pts, trimbox.y0 + m_pts, trimbox.x1 - m_pts, trimbox.y1 - m_pts)
    page.set_artbox(artbox)
    
    # Omit set_bleedbox to avoid "not in MediaBox" precision errors
    return doc, page, trimbox

def gen_ok_perfect():
    path = TEST_FOLDER / "01_perfect_ok.pdf"
    doc, page, trim = create_base_pdf("ok.pdf")
    page.insert_text((150, 150), "OK Perfect - Ready for Print", fontsize=20, color=(0, 0, 0))
    doc.save(str(path))
    doc.close()
    return path

def gen_err_rgb():
    path = TEST_FOLDER / "02_error_rgb_colorspace.pdf"
    doc, page, trim = create_base_pdf("rgb.pdf")
    # RGB Square in the center (Safe Area)
    page.draw_rect(fitz.Rect(200, 200, 400, 400), color=(1, 0, 0), fill=(1, 0, 0))
    page.insert_text((200, 450), "Erro de Cores: RGB Detectado", fontsize=15)
    doc.save(str(path))
    doc.close()
    return path

# ─── API Interaction Logic ──────────────────────────────────────────────────

def process_file(file_path: Path):
    print(f"\n[DEMO] Processando {file_path.name}...")
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/pdf")}
        data = {"client_locale": "pt-BR", "tipo_produto": "Papelaria Plana"}
        resp = requests.post(f"{API_BASE}/validate", files=files, data=data)
    
    if resp.status_code != 202:
        return {"filename": file_path.name, "error": f"Falha no upload: {resp.status_code}"}
    
    job_id = resp.json()["job_id"]
    
    # Polling
    status = "QUEUED"
    start_time = time.time()
    while status not in ["DONE", "FAILED", "GOLD_APPROVED", "GOLD_REJECTED"]:
        if time.time() - start_time > 120: return {"filename": file_path.name, "error": "Timeout"}
        time.sleep(3)
        status_resp = requests.get(f"{API_BASE}/jobs/{job_id}/status")
        status = status_resp.json()["status"]
        print(f"  Status: {status}")
    
    # Get Results
    report_resp = requests.get(f"{API_BASE}/jobs/{job_id}/report")
    report = report_resp.json()
    
    corrected_path = None
    if status == "GOLD_APPROVED":
        gold_resp = requests.get(f"{API_BASE}/jobs/{job_id}/gold")
        if gold_resp.status_code == 200:
            corrected_filename = file_path.stem + "_GOLD.pdf"
            corrected_path = CORRECTED_FOLDER / corrected_filename
            with open(corrected_path, "wb") as f:
                f.write(gold_resp.content)
            print(f"  Sucesso: Arquivo corrigido salvo em {corrected_filename}")
    
    return {
        "filename": file_path.name,
        "job_id": job_id,
        "status": report["status"],
        "erros": [e["codigo"] for e in report.get("erros", [])],
        "remediation_status": (status == "GOLD_APPROVED"),
        "corrected_file": corrected_path.name if corrected_path else "N/A"
    }

def run_demo():
    print("=== Graphic-Pro Demonstração Final (V5) ===")
    test_files = [gen_ok_perfect(), gen_err_rgb()]
    results = [process_file(f) for f in test_files]
    
    with open(REPORT_FILE, "w") as f:
        f.write("# Relatório Industrial Consolidado — Graphic-Pro\n\n")
        f.write("| Arquivo | Status | Erros | Corrigido | Link Gold |\n")
        f.write("|---|---|---|---|---|\n")
        for r in results:
            rem = "✅" if r["remediation_status"] else "❌"
            status = "✅ APROVADO" if r["status"] == "APROVADO" or r["remediation_status"] else "❌ REPROVADO"
            f.write(f"| {r['filename']} | {status} | {', '.join(r['erros'])} | {rem} | {r['corrected_file']} |\n")
            
    print(f"\nRelatório final atualizado em: {REPORT_FILE}")

if __name__ == "__main__":
    run_demo()

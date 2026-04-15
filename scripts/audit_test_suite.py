import requests
import time
import os
import json

API_BASE = "http://localhost:8001/api/v1"
TEST_DIR = "/home/diego/Downloads/graphic_pro_validation"
REPORT_OUT = os.path.join(TEST_DIR, "RELATORIO_AUDITORIA.md")

EXPECTATIONS = {
    "err_missing_bleed.pdf": ["G002_INSUFFICIENT_BLEED", "E002_MISSING_BLEED"],
    "err_rgb_colorspace.pdf": ["E006_RGB_COLORSPACE"],
    "err_low_res.pdf": ["E005_LOW_RESOLUTION", "E006_RASTER_LOW_RESOLUTION"],
    "err_transparency.pdf": ["W_OPACITY", "E005_ACTIVE_TRANSPARENCY"],
    "ok_perfect.pdf": [] # Should be APROVADO
}

def audit_file(filename):
    filepath = os.path.join(TEST_DIR, filename)
    print(f"\n[AUDIT] Processing {filename}...")
    
    # 1. Upload
    with open(filepath, "rb") as f:
        files = {"file": (filename, f, "application/pdf")}
        data = {"client_locale": "pt-BR"}
        resp = requests.post(f"{API_BASE}/validate", files=files, data=data)
    
    if resp.status_code != 202:
        return f"FAILED to upload: {resp.status_code} {resp.text}"
    
    job_id = resp.json()["job_id"]
    print(f"  Job ID: {job_id}")
    
    # 2. Polling
    status = "QUEUED"
    while status not in ["DONE", "FAILED"]:
        time.sleep(2)
        status_resp = requests.get(f"{API_BASE}/jobs/{job_id}/status")
        status = status_resp.json()["status"]
        print(f"  Status: {status}")
    
    if status == "FAILED":
        return "Job FAILED during processing"
    
    # 3. Get Report
    report_resp = requests.get(f"{API_BASE}/jobs/{job_id}/report")
    report = report_resp.json()
    
    # 4. Verify
    found_codes = [e["codigo"] for e in report.get("erros", [])] + \
                  [a["codigo"] for a in report.get("avisos", [])]
    
    expected_any = EXPECTATIONS.get(filename, [])
    
    result = {
        "filename": filename,
        "job_id": job_id,
        "final_status": report["status"],
        "found_codes": found_codes,
        "expected_codes": expected_any,
        "pass": False
    }
    
    if not expected_any:
        if report["status"] == "APROVADO":
            result["pass"] = True
    else:
        # Check if at least one of the expected codes was found
        if any(code in found_codes for code in expected_any):
            result["pass"] = True
            
    return result

def run_audit_suite():
    results = []
    files = [f for f in os.listdir(TEST_DIR) if f.endswith(".pdf")]
    
    for f in sorted(files):
        try:
            res = audit_file(f)
            results.append(res)
        except Exception as e:
            print(f"Error auditing {f}: {e}")
            results.append({"filename": f, "error": str(e), "pass": False})
            
    # Generate Markdown Report
    with open(REPORT_OUT, "w") as f:
        f.write("# Relatório de Auditoria de Validação\n\n")
        f.write(f"**Data**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| Arquivo | Status Final | Códigos Encontrados | Esperado | Resultado |\n")
        f.write("|---|---|---|---|---|\n")
        
        for r in results:
            if "error" in r:
                f.write(f"| {r['filename']} | ERROR | - | - | ❌ {r['error']} |\n")
                continue
                
            pass_str = "✅ PASS" if r["pass"] else "❌ FAIL"
            f.write(f"| {r['filename']} | {r['final_status']} | {', '.join(r['found_codes'])} | {', '.join(r['expected_codes'])} | {pass_str} |\n")
            
    print(f"\nAudit complete. Report saved to {REPORT_OUT}")

if __name__ == "__main__":
    run_audit_suite()

import os
import time
import requests
import concurrent.futures
from pathlib import Path

# Settings
API_URL = "http://localhost:8001/api/v1"
SOURCE_DIR = "/home/diego/Documents"
OUTPUT_DIR = "/home/diego/Documents/Corrigidos"
CONCURRENCY = 8 # Matches number of workers

def process_file(file_path):
    filename = os.path.basename(file_path)
    print(f"[START] Processing {filename}...")
    
    # 1. Upload
    try:
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{API_URL}/validate",
                files={"file": (filename, f, "application/pdf")},
                data={"client_locale": "pt-BR"}
            )
        
        if resp.status_code != 202:
            return {"file": filename, "status": "UPLOAD_FAILED", "error": resp.text}
        
        job_id = resp.json()["job_id"]
        print(f"[QUEUED] {filename} -> Job ID: {job_id}")
        
        # 2. Polling
        while True:
            status_resp = requests.get(f"{API_URL}/jobs/{job_id}/status")
            if status_resp.status_code != 200:
                return {"file": filename, "status": "POLL_FAILED", "error": status_resp.text}
            
            data = status_resp.json()
            status = data["status"]
            final_status = data.get("final_status")
            
            if status in ["DONE", "GOLD_APPROVED", "GOLD_REJECTED", "FAILED"]:
                print(f"[FINISHED] {filename} -> Status: {status}, Result: {final_status}")
                
                # 3. Download Result (if Gold)
                if status == "GOLD_APPROVED":
                    gold_resp = requests.get(f"{API_URL}/jobs/{job_id}/gold")
                    if gold_resp.status_code == 200:
                        gold_filename = f"{Path(filename).stem}_gold.pdf"
                        gold_path = os.path.join(OUTPUT_DIR, gold_filename)
                        with open(gold_path, "wb") as out_f:
                            out_f.write(gold_resp.content)
                        return {"file": filename, "status": "SUCCESS", "job_id": job_id, "gold": gold_filename}
                    else:
                        return {"file": filename, "status": "DOWNLOAD_FAILED", "error": gold_resp.text, "job_id": job_id}
                
                return {"file": filename, "status": "FINISHED_NO_GOLD", "job_id": job_id, "result": final_status}
            
            time.sleep(2)
            
    except Exception as e:
        return {"file": filename, "status": "EXCEPTION", "error": str(e)}

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    pdfs = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR) if f.lower().endswith(".pdf")]
    print(f"Found {len(pdfs)} PDF files in {SOURCE_DIR}")
    
    start_total = time.time()
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = {executor.submit(process_file, pdf): pdf for pdf in pdfs}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            
    end_total = time.time()
    
    print("\n" + "="*50)
    print(" STRESS TEST RESULTS ")
    print("="*50)
    for res in results:
        icon = "✅" if res["status"] == "SUCCESS" else "⚠️" if res["status"] == "FINISHED_NO_GOLD" else "❌"
        print(f"{icon} {res['file']}: {res['status']} {res.get('error', '')}")
    
    print(f"\nTotal time: {end_total - start_total:.2f}s")
    
    # Save a simple report
    with open(os.path.join(OUTPUT_DIR, "STRESS_TEST_LOG.txt"), "w") as f:
        f.write("STRESS TEST LOG\n")
        f.write("="*20 + "\n")
        for res in results:
            f.write(f"{res['file']} | {res['status']} | {res.get('job_id', 'N/A')}\n")

if __name__ == "__main__":
    main()

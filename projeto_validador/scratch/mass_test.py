import requests
import time
import os
import sys
from pathlib import Path

BASE_URL = "http://localhost:8001/api/v1"
TEST_FOLDER = "/home/diego/Documents/ARQUIVOS_TESTE"

def get_token():
    try:
        r = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin@admin", "password": "admin"})
        r.raise_for_status()
        return r.json()["access_token"]
    except Exception as e:
        print(f"Erro ao obter token: {e}")
        sys.exit(1)

def upload_file(file_path, token):
    try:
        with open(file_path, "rb") as f:
            # Especificar o filename e o content-type para evitar 415 Unsupported Media Type
            files = {
                "file": (os.path.basename(file_path), f, "application/pdf")
            }
            r = requests.post(
                f"{BASE_URL}/validate",
                headers={"Authorization": f"Bearer {token}"},
                files=files
            )
        r.raise_for_status()
        return r.json()["job_id"]
    except Exception as e:
        print(f"Erro ao subir {os.path.basename(file_path)}: {e}")
        return None

def monitor_jobs(job_ids, token):
    active_jobs = list(job_ids)
    results = {}
    
    print(f"\nMonitorando {len(active_jobs)} jobs...\n")
    
    while active_jobs:
        for jid in list(active_jobs):
            try:
                r = requests.get(
                    f"{BASE_URL}/jobs/{jid}/status",
                    headers={"Authorization": f"Bearer {token}"}
                )
                r.raise_for_status()
                status_data = r.json()
                status = status_data["status"]
                
                if status in ("DONE", "FAILED"):
                    print(f"Job {jid} finalizado: {status}")
                    results[jid] = status
                    active_jobs.remove(jid)
                else:
                    err_count = status_data.get("error_count", 0)
                    print(f"Job {jid}: {status} (Erros: {err_count})", end="\r")
            except Exception as e:
                print(f"\nErro ao monitorar {jid}: {e}")
        
        if active_jobs:
            time.sleep(5)
            
    return results

def main():
    token = get_token()
    files = [os.path.join(TEST_FOLDER, f) for f in os.listdir(TEST_FOLDER) if f.endswith(".pdf")]
    
    if not files:
        print("Nenhum arquivo PDF encontrado.")
        return

    job_ids = []
    print(f"Iniciando upload de {len(files)} arquivos...")
    for f in files:
        jid = upload_file(f, token)
        if jid:
            print(f"Submetido: {os.path.basename(f)} -> {jid}")
            job_ids.append(jid)
    
    if job_ids:
        monitor_jobs(job_ids, token)
        print("\n--- Teste de Massa Concluído ---")

if __name__ == "__main__":
    main()

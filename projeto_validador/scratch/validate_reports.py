import requests
import time
import os
import sys

BASE_URL = "http://localhost:8001/api/v1"
TEST_FOLDER = "/home/diego/Documents/ARQUIVOS_TESTE"

def get_token():
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin@admin", "password": "admin"})
    r.raise_for_status()
    return r.json()["access_token"]

def upload_file(file_path, token):
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/pdf")}
        r = requests.post(f"{BASE_URL}/validate", headers={"Authorization": f"Bearer {token}"}, files=files)
    r.raise_for_status()
    return r.json()["job_id"]

def wait_for_jobs(job_ids, token):
    active_jobs = list(job_ids)
    while active_jobs:
        for jid in list(active_jobs):
            r = requests.get(f"{BASE_URL}/jobs/{jid}/status", headers={"Authorization": f"Bearer {token}"})
            status = r.json()["status"]
            if status in ("DONE", "FAILED", "GOLD_DELIVERED", "GOLD_DELIVERED_WITH_WARNINGS", "GOLD_REJECTED"):
                active_jobs.remove(jid)
        if active_jobs:
            time.sleep(2)

def fetch_reports(jobs, token):
    print("\n" + "="*60)
    print("ANÁLISE DE RELATÓRIOS")
    print("="*60)
    for filename, jid in jobs.items():
        try:
            r = requests.get(f"{BASE_URL}/jobs/{jid}/report", headers={"Authorization": f"Bearer {token}"})
            report = r.json()
            status = report.get("status", "UKNOWN")
            erros = report.get("erros", [])
            print(f"\nArquivo: {filename}")
            print(f"Status Final: {status}")
            print(f"Qtd Erros Críticos: {len(erros)}")
            
            if erros:
                print("Erros Encontrados:")
                for erro in erros:
                    print(f"  - [{erro.get('codigo')}] {erro.get('titulo')}")
                    print(f"    Encontrado: {erro.get('found_value')} | Esperado: {erro.get('expected_value')}")
            else:
                print("Nenhum erro encontrado.")
        except Exception as e:
            print(f"\nArquivo: {filename} -> Falha ao obter relatório: {e}")

if __name__ == "__main__":
    token = get_token()
    files = sorted([f for f in os.listdir(TEST_FOLDER) if f.endswith(".pdf")])
    
    jobs = {}
    print("Submetendo arquivos para validação...")
    for f in files:
        filepath = os.path.join(TEST_FOLDER, f)
        jid = upload_file(filepath, token)
        jobs[f] = jid
        print(f" > {f} -> {jid}")
        
    print("\nAguardando processamento do pipeline...")
    wait_for_jobs(jobs.values(), token)
    
    fetch_reports(jobs, token)

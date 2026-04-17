import os
import requests
import time
import json
from pathlib import Path

BASE_URL = "http://localhost:8001/api/v1"
BASE_DIR = "/home/diego/Downloads/GWG-cert/Ghent_PDF_Output_Suite_V50_Patches/Categories"

def get_token():
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin@admin", "password": "admin"})
    r.raise_for_status()
    return r.json()["access_token"]

def upload_file(file_path, token):
    with open(file_path, "rb") as f:
        # Extrair categoria do caminho
        parts = file_path.parts
        category = "unknown"
        for p in parts:
            if p in ["1-CMYK", "2-SPOT", "3-ICC-CMS"]:
                category = p
                break
                
        files = {"file": (file_path.name, f, "application/pdf")}
        # Adicionar metadados para ajudar no roteamento (opcional)
        r = requests.post(f"{BASE_URL}/validate", 
                         headers={"Authorization": f"Bearer {token}"}, 
                         files=files)
        r.raise_for_status()
        return r.json()["job_id"], category

def run_test():
    token = get_token()
    patches = []
    
    print("Localizando patches...")
    for root, dirs, files in os.walk(BASE_DIR):
        if "Patches" in root:
            for f in files:
                if f.endswith(".pdf") and "_ReadMe" not in f and "Test page" not in f:
                    patches.append(Path(root) / f)
                    
    print(f"Encontrados {len(patches)} patches. Iniciando submissão...")
    
    jobs = []
    for p in patches:
        try:
            jid, cat = upload_file(p, token)
            jobs.append({"job_id": jid, "filename": p.name, "category": cat, "status": "QUEUED"})
            print(f"Submetido [{cat}]: {p.name} -> {jid}")
        except Exception as e:
            print(f"Erro ao submeter {p.name}: {e}")
            
    # Salvar rastro inicial
    with open("scratch/gwg_patches_jobs.json", "w") as f:
        json.dump(jobs, f, indent=2)
        
    print("\nTodos os arquivos foram submetidos. Monitoramento em andamento via script externo.")

if __name__ == "__main__":
    run_test()

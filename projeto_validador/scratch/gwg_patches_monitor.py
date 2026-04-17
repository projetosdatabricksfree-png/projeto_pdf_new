import os
import requests
import time
import json
from rich.console import Console
from rich.table import Table

BASE_URL = "http://localhost:8001/api/v1"

def get_token():
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin@admin", "password": "admin"})
    r.raise_for_status()
    return r.json()["access_token"]

def monitor():
    token = get_token()
    
    if not os.path.exists("scratch/gwg_patches_jobs.json"):
        print("Arquivo de jobs não encontrado.")
        return

    with open("scratch/gwg_patches_jobs.json", "r") as f:
        jobs = json.load(f)

    total = len(jobs)
    console = Console()

    print(f"Monitorando {total} jobs...")

    while True:
        done_count = 0
        results = []
        
        for j in jobs:
            if j["status"] in ["DONE", "FAILED", "GOLD_DELIVERED", "GOLD_DELIVERED_WITH_WARNINGS"]:
                done_count += 1
                continue
            
            try:
                r = requests.get(f"{BASE_URL}/jobs/{j['job_id']}/status", headers={"Authorization": f"Bearer {token}"})
                r.raise_for_status()
                data = r.json()
                j["status"] = data["status"]
                if j["status"] in ["DONE", "FAILED", "GOLD_DELIVERED", "GOLD_DELIVERED_WITH_WARNINGS"]:
                    done_count += 1
            except Exception as e:
                pass

        print(f"Progresso: {done_count}/{total} concluídos.", end="\r")
        
        if done_count == total:
            break
        time.sleep(10)

    print("\n\nProcessamento concluído. Coletando vereditos finais...")
    
    table = Table(title="Resultado Patches GWG v5.0")
    table.add_column("Categoria", style="cyan")
    table.add_column("Arquivo", style="white")
    table.add_column("Status Final", style="green")
    table.add_column("Erros", style="red")

    final_results = []
    for j in jobs:
        try:
            r = requests.get(f"{BASE_URL}/jobs/{j['job_id']}/report", headers={"Authorization": f"Bearer {token}"})
            report = r.json()
            err_count = len(report.get("erros", []))
            table.add_row(j["category"], j["filename"], j["status"], str(err_count))
            final_results.append({
                "category": j["category"],
                "filename": j["filename"],
                "status": j["status"],
                "errors": report.get("erros", [])
            })
        except:
            table.add_row(j["category"], j["filename"], j["status"], "N/A")

    console.print(table)
    
    with open("scratch/gwg_patches_results.json", "w") as f:
        json.dump(final_results, f, indent=2)

if __name__ == "__main__":
    monitor()

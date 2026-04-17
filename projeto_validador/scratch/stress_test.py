import os
import shutil
import time
import requests
import time
import requests
from concurrent.futures import ThreadPoolExecutor

TEST_FOLDER = "/home/diego/Documents/ARQUIVOS_TESTE"
BASE_URL = "http://localhost:8001/api/v1"

# 1. Copiar arquivos base para criar 200 PDFs
base_files = [f for f in os.listdir(TEST_FOLDER) if f.endswith('.pdf') and not f[0].isdigit() * 3]
if not base_files:
    # caso já tenha renomeado, pegar os primeiros 6
    base_files = sorted([f for f in os.listdir(TEST_FOLDER) if f.endswith('.pdf')])[:6]

print(f"Bases identificadas: {base_files}")

# Limpar arquivos gerados em testes anteriores (que começam com 3 dígitos numéricos)
for f in os.listdir(TEST_FOLDER):
    if f.endswith('.pdf') and f[:3].isdigit():
        os.remove(os.path.join(TEST_FOLDER, f))

# Gerar 200 arquivos
expected_results = {}
created_files = []
for i in range(1, 201):
    base = base_files[i % len(base_files)]
    new_name = f"{i:03d}_{base}"
    shutil.copy2(os.path.join(TEST_FOLDER, base), os.path.join(TEST_FOLDER, new_name))
    created_files.append(new_name)
    
    # Definindo a expectativa baseada no nome
    if "perfect_ok" in base:
        expected_results[new_name] = {"expected_status": "REPROVADO"} # pq synthetic nao tem ICC
    elif "warn" in base:
        expected_results[new_name] = {"expected_status": "REPROVADO"} 
    else:
        expected_results[new_name] = {"expected_status": "REPROVADO"} 

print(f"Gerados 200 arquivos PDF em {TEST_FOLDER}")

# 2. Upload paralelo
def get_token():
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin@admin", "password": "admin"})
    r.raise_for_status()
    return r.json()["access_token"]

token = get_token()

def upload_file(filename):
    filepath = os.path.join(TEST_FOLDER, filename)
    with open(filepath, "rb") as f:
        files = {"file": (filename, f, "application/pdf")}
        r = requests.post(f"{BASE_URL}/validate", headers={"Authorization": f"Bearer {token}"}, files=files)
        r.raise_for_status()
        jid = r.json()["job_id"]
        print(f"Upload: {filename} -> {jid}")
        return filename, jid

def mass_upload(files_list):
    jobs = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        for fname, jid in executor.map(upload_file, files_list):
            jobs[fname] = jid
    return jobs

print("Iniciando uploads concorrentes (10 threads)...")
jobs = mass_upload(created_files)

# 3. Polling de Status
print(f"Aguardando o processamento de {len(jobs)} arquivos (Isso vai estressar os workers)...")
active_jobs = list(jobs.values())
start_time = time.time()

while active_jobs:
    for jid in list(active_jobs):
        try:
            r = requests.get(f"{BASE_URL}/jobs/{jid}/status", headers={"Authorization": f"Bearer {token}"})
            status = r.json()["status"]
            if status in ("DONE", "FAILED", "GOLD_DELIVERED", "GOLD_DELIVERED_WITH_WARNINGS", "GOLD_REJECTED"):
                active_jobs.remove(jid)
        except Exception:
            pass # ignore timeouts during heavy load polling
    
    elapsed = time.time() - start_time
    print(f"[{int(elapsed)}s] Jobs pendentes: {len(active_jobs)}")
    if active_jobs:
        time.sleep(5)

print(f"Processamento concluído em {time.time() - start_time:.1f} segundos!")

# 4. Check Divergences
print("Analisando resultados...")
divergences = []
for fname, jid in jobs.items():
    try:
        r = requests.get(f"{BASE_URL}/jobs/{jid}/report", headers={"Authorization": f"Bearer {token}"})
        result = r.json()
        real_status = result.get("status", "UKNOWN")
        expected = expected_results[fname]["expected_status"]
        
        if real_status != expected:
            divergences.append(f"DIVERGÊNCIA em {fname}: Esperado {expected}, Obtido {real_status}")
    except Exception as e:
        divergences.append(f"ERRO em {fname}: falha ao obter relatório -> {e}")

print("=" * 50)
if not divergences:
    print("✅ SUCESSO ABSOLUTO! Sem divergências. Todos os 200 PDFs processados perfeitamente conforme esperado.")
else:
    print(f"❌ ENCONTRADAS {len(divergences)} DIVERGÊNCIAS:")
    for d in divergences:
        print(d)
print("=" * 50)

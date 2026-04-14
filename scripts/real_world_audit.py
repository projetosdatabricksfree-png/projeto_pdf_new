import os
import requests
import time
import uuid
from pathlib import Path

# Configurações do Ambiente Real
BASE_URL = "http://localhost:8001"
API_UPLOAD = f"{BASE_URL}/api/v1/validate"
GWG_DIR = "/home/diego/Downloads/GWG-cert/Ghent_PDF_Output_Suite_V50_Patches/Categories"

def run_real_world_audit():
    pdf_files = []
    for root, _, files in os.walk(GWG_DIR):
        for f in files:
            if f.lower().endswith('.pdf') and 'readme' not in f.lower():
                # Filtrando apenas arquivos de patches reais para evitar poluição
                pdf_files.append(os.path.join(root, f))
    pdf_files.sort()

    print(f"🚀 Iniciando Simulação de Vida Real (Operador Bot): {len(pdf_files)} patches.")
    print(f"📡 Conectando ao Backend: {BASE_URL}")
    
    master_report = "# P R E F L I G H T   I N S P E C T O R  ·  A U D I T O R I A   D E   V I D A   R E A L\n"
    master_report += "### Certificação GWG 2015 via Roteamento Inteligente\n\n"
    master_report += f"Este laudo reflete fielmente o comportamento da Colmeia de Agentes operando de forma autônoma.\n\n"

    for i, path in enumerate(pdf_files):
        fname = os.path.basename(path)
        print(f"[{i+1}/{len(pdf_files)}] Enviando para Recepção: {fname}")
        
        try:
            # 1. Fazendo o Upload "Cego" (Simulando o Operador)
            with open(path, 'rb') as f:
                response = requests.post(
                    API_UPLOAD,
                    files={'file': (fname, f, 'application/pdf')},
                    data={'client_locale': 'pt-BR'}
                )
            
            if response.status_code != 202:
                print(f"  ❌ Falha no Upload: {response.status_code} - {response.text}")
                continue
                
            job_data = response.json()
            job_id = job_data['job_id']
            status_url = f"{BASE_URL}/api/v1/jobs/{job_id}/status"
            report_url = f"{BASE_URL}/api/v1/jobs/{job_id}/report"
            
            # 2. Polling de Status (Esperando a Colmeia decidir e processar)
            start_time = time.time()
            final_status_data = None
            while True:
                status_res = requests.get(status_url)
                if status_res.status_code == 200:
                    status_info = status_res.json()
                    if status_info['status'] == 'DONE':
                        final_status_data = status_info
                        break
                    if status_info['status'] == 'FAILED':
                        print(f"  ❌ Job falhou no pipe do Celery.")
                        break
                
                if time.time() - start_time > 120: # Timeout de 2 min
                    print(f"  ⚠️ Timeout aguardando o processamento do patch.")
                    break
                time.sleep(0.5)
            
            if not final_status_data:
                continue

            # 3. Capturando o Laudo Oficial da Inteligência
            report_res = requests.get(report_url)
            if report_res.status_code != 200:
                print(f"  ⚠️ Não foi possível capturar o laudo final para {job_id}")
                continue
                
            report = report_res.json()
            
            # 4. Consolidando no Markdown (Vidal Real)
            duration = report.get('tempo_processamento_ms', 0)
            status_msg = report.get('status', 'UNKNOWN')
            agente = report.get('agente_processador', 'Autônomo')
            produto = report.get('produto', fname)
            
            emoji = "❌" if status_msg == "REPROVADO" else "✅"
            rel = f"## {emoji} {status_msg}: {fname}\n"
            rel += f"**Produto Detectado**: {produto} | **Agente Selecionado**: `{agente}` | **Tempo**: {duration}ms\n\n"
            
            rel += f"### Resumo do Sistema\n"
            rel += f"{report.get('resumo', 'Sem resumo disponível.')}\n\n"
            
            rel += "| CHECK | CÓDIGO | ENCONTRADO | ESPERADO | PÁGINAS | STATUS |\n"
            rel += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            
            detalhes = report.get('detalhes_tecnicos', {})
            # Se detalhes for uma lista (novo padrão) ou dict
            if isinstance(detalhes, dict):
                for code, d in detalhes.items():
                    status_icon = "🟢" if d.get('status') == 'OK' else "🔴" if d.get('status') == 'ERRO' else "🟡"
                    found = str(d.get('found_value'))[:30]
                    rel += f"| {d.get('label', code)} | {d.get('error_code', code)} | {found} | {str(d.get('expected_value'))[:25]} | {str(d.get('paginas', '-'))} | {status_icon} {d.get('status')} |\n"
            
            rel += f"\n---\n\n"
            master_report += rel
            print(f"  ✅ Concluído via {agente} em {duration}ms")

        except Exception as e:
            print(f"  ❌ Erro de Conexão na Simulação: {e}")

    output_path = '/home/diego/Desktop/PROJETOS/Projeto_grafica/docs/SPRINT_QA/RELATORIO_VIDA_REAL_FINAL.md'
    with open(output_path, 'w') as f:
        f.write(master_report)
    print(f"✅ Auditoria de Vida Real Finalizada: {output_path}")

if __name__ == "__main__":
    run_real_world_audit()

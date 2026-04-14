import os
import sys
import json
import time
import uuid
from pathlib import Path

# Ajustando caminhos para o ambiente interno do Container
sys.path.append('/app')

try:
    from agentes.operarios.shared_tools.gwg.run_full_suite import run_all_gwg_checks
except ImportError as e:
    print(f"❌ Erro ao importar o Orquestrador Oficial no Container: {e}")
    sys.exit(1)

# Perfil de Rigor Industrial GWG 2015 (O mesmo do SaaS)
FULL_PROFILE = {
    'name': 'GWG 2015 Default (Generic)',
    'tac_limit': 300,
    'min_image_resolution': 150,
    'warn_image_resolution': 225,
    'max_spot_colors': 2,
    'allowed_color_spaces': ['CMYK', 'Gray', 'Spot'],
    'allow_rgb': False
}

def get_action_recommendation(label, status):
    if str(status).upper() == 'OK': return 'Manter padrão atual.'
    l = str(label).lower()
    if 'geometry' in l or 'box' in l: return 'Ajuste os boxes de página (Trim/Bleed).'
    if 'font' in l: return 'Incorpore todas as fontes antes de exportar.'
    if 'color' in l or 'tac' in l: return 'Excesso de tinta ou espaço proibido. Re-converta.'
    if 'compression' in l: return 'Salve com imagem alta (mín. 80%).'
    if 'transparency' in l: return 'Achate as transparências.'
    return 'Consulte seu designer/pré-impressão.'

def generate_report():
    base_dir = '/app/audit_data'
    pdf_files = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.lower().endswith('.pdf') and 'readme' not in f.lower():
                pdf_files.append(os.path.join(root, f))
    pdf_files.sort()

    print(f"🚀 Iniciando Auditoria Full (MAS In-Container): {len(pdf_files)} patches.")
    master_report = ""

    for i, path in enumerate(pdf_files):
        fname = os.path.basename(path)
        rel_path = os.path.relpath(path, base_dir)
        cat = rel_path.split(os.sep)[0] if os.sep in rel_path else "Root"
        
        job_id = str(uuid.uuid4())[:8].upper()
        print(f"[{i+1}/{len(pdf_files)}] Processando: {fname}")
        
        try:
            start_time = time.time()
            engine_result = run_all_gwg_checks(path, profile=FULL_PROFILE, job_id=job_id)
            duration_ms = int((time.time() - start_time) * 1000)
            
            normalized = engine_result.get('normalized', [])
            erros_codigos = engine_result.get('erros', [])
            avisos_codigos = engine_result.get('avisos', [])
            
            erros = [r for r in normalized if r['status'] == 'ERRO']
            avisos = [r for r in normalized if r['status'] == 'AVISO']
            oks = [r for r in normalized if r['status'] == 'OK']
            
            score = int((len(oks) / len(normalized) * 100)) if normalized else 0
            status_msg = 'REPROVADO' if erros_codigos else 'APROVADO' if not avisos_codigos else 'APROVADO_COM_RESSALVAS'
            
            rel = f"# P R E F L I G H T   I N S P E C T O R  ·  R E L A T Ó R I O   D E   V A L I D A Ç Ã O\n"
            rel += f"**{cat}** ({FULL_PROFILE['name']})\n"
            rel += f"Job: `{job_id}`  ·  {time.strftime('%d/%m/%Y')}  ·  Agentes Especialistas: 9 em Paralelo (Billiard)  ·  {duration_ms}ms\n\n"
            
            emoji = "❌" if status_msg == "REPROVADO" else "✅"
            rel += f"## {emoji} {status_msg}\n"
            rel += f"# {score}%\n"
            rel += f"SCORE DE QUALIDADE (COLMEIA)\n\n"
            
            rel += f"### Resumo Executivo\n"
            if erros:
                rel += f"A Colmeia de Agentes identificou {len(erros)} falha(s) técnica(s) grave(s).\n\n"
            else:
                rel += f"Sistema validado por 9 especialistas. Arquivo em conformidade.\n\n"
            
            rel += f"| {len(erros)} | {len(avisos)} | {len(oks)} | {len(normalized)} |\n"
            rel += f"| :---: | :---: | :---: | :---: |\n"
            rel += f"| **Erros Críticos** | **Avisos** | **Checks OK** | **Total Verificado** |\n\n"
            
            if erros:
                rel += f"#### ⛔ Erros Detectados pelos Agentes\n"
                for e in erros:
                    rel += f"- **{e['label']}** (Cód: {e['codigo']}): {get_action_recommendation(e['label'], 'ERRO')} (Recurso: Pág {e.get('page', '-')})\n"
                rel += '\n'

            rel += "### Tabela Técnica de Auditoria (Normalizada)\n"
            rel += "| AGENTE | CÓDIGO | ENCONTRADO | ESPERADO | PÁGINA | STATUS |\n"
            rel += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for r in normalized:
                status_icon = "🟢" if r['status'] == 'OK' else "🔴" if r['status'] == 'ERRO' else "🟡"
                found = str(r['found_value'])[:30] if r['found_value'] else "Conforme"
                rel += f"| {r['label']} | {r['codigo']} | {found} | {str(r['expected_value'])[:25]} | {r.get('page', '-')} | {status_icon} {r['status']} |\n"
            
            rel += f"\nPreFlight Inspector · Arquitetura Multi-Agente · Gerado em {time.strftime('%d/%m/%Y, %H:%M:%S')}\n"
            rel += "\n---\n\n"
            master_report += rel
            
        except Exception as exc:
            print(f"  ❌ Falha crítica no orquestrador para {fname}: {exc}")

    output_path = '/app/RELATORIO_AUDITORIA_AGENTES_FINAL.md'
    with open(output_path, 'w') as f:
        f.write(master_report)
    print(f"✅ Auditoria Final In-Container concluída: {output_path}")

if __name__ == "__main__":
    generate_report()

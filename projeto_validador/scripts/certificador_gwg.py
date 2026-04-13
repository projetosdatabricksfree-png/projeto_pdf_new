"""
GWG Certification Script - Preflight Validator
Runs the system against the official Ghent PDF Output Suite 5.0 patches.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.append(str(Path(__file__).parent.parent))

from agentes.operarios.shared_tools.gwg.color_checker import check_color_compliance
from agentes.operarios.shared_tools.gwg.opm_checker import check_opm as check_white_overprint
from agentes.operarios.shared_tools.gwg.geometry_checker import check_geometry
from agentes.operarios.shared_tools.gwg.profile_matcher import identify_profile_by_metadata

TEST_DIR = "/home/diego/Desktop/PROJETOS/Testes/Arquivos_Teste_Projeto_Grafica"
GOLD_FILE = "Ghent_PDF-Output-Test-V50_ALL_X4.pdf"

def run_certification(file_path: str = None):
    if not file_path:
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
        else:
            file_path = str(Path(TEST_DIR) / GOLD_FILE)
    
    target = Path(file_path)
    
    if not target.exists():
        print(f"ERRO: Arquivo de teste não encontrado em {target}")
        return

    print(f"\n{'='*60}")
    print(f" CERTIFICAÇÃO GWG 2022 - DIAGNÓSTICO PROFUNDO ")
    print(f" Alvo: {GOLD_FILE}")
    print(f"{'='*60}\n")

    metadata = {"produto": "Cartão de Visita Premium"} # Perfil Sheetfed por padrão
    
    # 1. Geometria (Trim/Bleed)
    print("[1/3] Validando Geometria (TrimBox/BleedBox)...")
    geo_results = check_geometry(str(target))
    for res in geo_results[:1]: # Mostra apenas a primeira página do teste
        for check in res["checks"]:
            status_icon = "✅" if check["status"] == "OK" else "⚠️" if check["status"] == "AVISO" else "❌"
            print(f"  {status_icon} {check['label']}: {check['value']} (Esperado: {check['expected']})")

    # 2. Metadados e Intenção de Saída (PDF/X-4)
    print("\n[2/4] Validando Metadados (Output Intent PDF/X-4)...")
    from agentes.operarios.shared_tools.gwg.icc_checker import check_icc
    icc_results = check_icc(str(target))
    icc_icon = "✅" if icc_results["status"] == "OK" else "❌"
    print(f"  {icc_icon} Output Intent: {icc_results.get('descricao', 'Perfil detectado')}")

    # 3. Cores e TAC
    print("\n[3/4] Validando Espaços de Cor e TAC (Ghostscript/VIPS)...")
    color_results = check_color_compliance(str(target), metadata)
    cs = color_results["color_space"]
    tac = color_results["tac"]
    
    cs_icon = "✅" if cs["status"] == "OK" else "❌"
    print(f"  {cs_icon} Espaço de Cor: {cs.get('valor', cs.get('valor_found'))}")
    
    tac_icon = "✅" if tac["status"] == "OK" else "❌"
    print(f"  {tac_icon} TAC Máximo: {tac.get('valor', tac.get('valor_found'))} (Limite: 300%)")

    # 4. White Overprint (Critério de Ouro do GWG 5.0)
    print("\n[4/4] Validando White Overprint (Patch 4.0.1)...")
    white_results = check_white_overprint(str(target))
    if white_results["status"] == "ERRO":
        print(f"  ❌ FALHA: {white_results['descricao']}")
    else:
        print(f"  ✅ SUCESSO: Nenhum White Overprint detectado.")

    print(f"\n{'='*60}")
    # Resultado Final agora exige OK em TODOS os itens críticos
    is_conforme = (
        all(c["status"] == "OK" for c in geo_results[0]["checks"]) and
        icc_results["status"] == "OK" and
        cs["status"] == "OK" and
        tac["status"] == "OK" and
        white_results["status"] == "OK"
    )
    print(f" RESULTADO FINAL: {'CONFORME' if is_conforme else 'NÃO CONFORME'}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run_certification()

import json
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.append("/home/diego/Desktop/PROJETOS/Projeto_grafica/projeto_validador")

from agentes.operarios.shared_tools.gwg.run_full_suite import run_all_gwg_checks

def dry_run_cert():
    # Target: A specific transparency patch for Sprint 4 validation
    target_patch = "/home/diego/Downloads/GWG-cert/Ghent_PDF_Output_Suite_V50_Patches/Categories/1-CMYK/ReadMes/GWG160-162_Transp_Basic_BM_DeviceCMYK_ReadMe.pdf"
    
    if not os.path.exists(target_patch):
        # Fallback to the master test page if the specific patch path is messy
        target_patch = "/home/diego/Downloads/GWG-cert/Ghent_PDF_Output_Suite_V50_Patches/Categories/1-CMYK/Test pages/Ghent_PDF-Output-Test-V50_CMYK_X4.pdf"

    print(f"🚀 [DRY-RUN] Processando Patch: {os.path.basename(target_patch)}")
    
    # Standard profile for certification: MagazineAds_CMYK (GWG 2015)
    default_profile = {"name": "MagazineAds_CMYK", "variant": "CMYK"}
    
    start_time = time.time()
    try:
        results = run_all_gwg_checks(target_patch, default_profile, job_id="DRY_RUN_CERT_001")
        duration = time.time() - start_time
        
        # Format Raw Output
        report = f"# RELATÓRIO DE CERTIFICAÇÃO GWG 5.0 (DRY-RUN)\n\n"
        report += f"**Arquivo:** `{target_patch}`\n"
        report += f"**Duração:** {duration:.2f}s\n"
        report += f"**Status Final:** {'OK/AVISO' if not any(r.get('status') == 'ERRO' for r in results) else 'REPROVADO'}\n\n"
        report += "## JSON BRUTO DE SAÍDA\n"
        report += "```json\n"
        report += json.dumps(results, indent=2, ensure_ascii=False)
        report += "\n```\n"
        
        with open("DRY_RUN_CERT_RESULT.md", "w") as f:
            f.write(report)
            
        print(f"✅ Dry-run concluído. Resultados salvos em DRY_RUN_CERT_RESULT.md")
        
    except Exception as e:
        print(f"❌ Erro no Dry-run: {e}")

if __name__ == "__main__":
    dry_run_cert()

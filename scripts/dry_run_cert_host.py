import json
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.append("/home/diego/Desktop/PROJETOS/Projeto_grafica/projeto_validador")

# Import checkers
from agentes.operarios.shared_tools.gwg.compression_checker import check_compression
from agentes.operarios.shared_tools.gwg.icc_checker import check_icc
from agentes.operarios.shared_tools.gwg.transparency_checker import check_transparency_gwg
from agentes.operarios.shared_tools.gwg.opm_checker import check_opm

def dry_run_cert_host():
    # Target: CMYK Test Page (The big one)
    target_patch = "/home/diego/Downloads/GWG-cert/Ghent_PDF_Output_Suite_V50_Patches/Categories/1-CMYK/Test pages/Ghent_PDF-Output-Test-V50_CMYK_X4.pdf"
    
    if not os.path.exists(target_patch):
        target_patch = "/home/diego/Downloads/GWG-cert/Ghent_PDF_Output_Suite_V50_Patches/Categories/1-CMYK/ReadMes/GWG160-162_Transp_Basic_BM_DeviceCMYK_ReadMe.pdf"

    print(f"🚀 [HOST-DRY-RUN V4] Processando Patch: {os.path.basename(target_patch)}")
    
    default_profile = {"name": "MagazineAds_CMYK", "variant": "CMYK"}
    
    start_time = time.time()
    results = []
    
    try:
        # Run checkers manual & synchronous
        print("- Transparency...")
        results.extend(check_transparency_gwg(target_patch, default_profile))
        
        print("- ICC...")
        results.extend(check_icc(target_patch, default_profile))
        
        print("- Compression...")
        results.extend(check_compression(target_patch, default_profile))
        
        print("- OPM...")
        results.extend(check_opm(target_patch, default_profile))

        duration = time.time() - start_time
        
        # Robust status check
        has_error = False
        for r in results:
            if isinstance(r, dict) and str(r.get("status", "")).upper() == "ERRO":
                has_error = True
                break

        # Format Raw Output
        report = f"# RELATÓRIO DE CERTIFICAÇÃO GWG 5.0 (DRY-RUN)\n\n"
        report += f"**Arquivo:** `{target_patch}`\n"
        report += f"**Duração:** {duration:.2f}s\n"
        report += f"**Status Final:** {'REPROVADO' if has_error else 'APROVADO/AVISO'}\n\n"
        report += "## JSON BRUTO DE SAÍDA\n"
        report += "```json\n"
        report += json.dumps(results, indent=2, ensure_ascii=False)
        report += "\n```\n"
        
        with open("DRY_RUN_CERT_RESULT.md", "w") as f:
            f.write(report)
            
        print(f"✅ Dry-run concluído com sucesso!")
        
    except Exception as e:
        import traceback
        print(f"❌ Erro fatal no Dry-run: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    dry_run_cert_host()

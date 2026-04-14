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

def run_mass_certification():
    base_dir = "/home/diego/Downloads/GWG-cert/Ghent_PDF_Output_Suite_V50_Patches"
    pdf_files = []
    
    # 1. Find all PDFs
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(".pdf") and "readme" not in file.lower():
                pdf_files.append(os.path.join(root, file))
    
    pdf_files.sort()
    
    print(f"📦 Localizados {len(pdf_files)} patches para certificação.")
    
    report_content = "# RELATÓRIO FINAL DE CERTIFICAÇÃO GWG 5.0\n"
    report_content += f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    report_content += "---\n\n"
    
    all_results = {}
    
    default_profile = {"name": "MagazineAds_CMYK", "variant": "CMYK"}
    
    for i, pdf_path in enumerate(pdf_files):
        filename = os.path.basename(pdf_path)
        print(f"[{i+1}/{len(pdf_files)}] Processando: {filename}...")
        
        file_results = []
        try:
            # Run the suite
            file_results.extend(check_transparency_gwg(pdf_path, default_profile))
            file_results.extend(check_icc(pdf_path, default_profile))
            file_results.extend(check_compression(pdf_path, default_profile))
            file_results.extend(check_opm(pdf_path, default_profile))
            
            all_results[filename] = file_results
            
            # Append to Markdown
            report_content += f"## Arquivo: `{filename}`\n"
            report_content += f"**Caminho:** `{pdf_path}`\n\n"
            report_content += "### Resultados Brutos:\n"
            report_content += "```json\n"
            report_content += json.dumps(file_results, indent=2, ensure_ascii=False)
            report_content += "\n```\n\n---\n\n"
            
        except Exception as e:
            print(f"  ❌ Erro ao processar {filename}: {e}")
            all_results[filename] = {"error": str(e)}

    # Final Save
    output_md = "/home/diego/Desktop/PROJETOS/Projeto_grafica/docs/SPRINT_QA/CERTIFICACAO_GWG_FINAL.md"
    os.makedirs(os.path.dirname(output_md), exist_ok=True)
    
    with open(output_md, "w") as f:
        f.write(report_content)
        
    print(f"\n✅ CERTIFICAÇÃO CONCLUÍDA!")
    print(f"📄 Relatório gerado em: {output_md}")

if __name__ == "__main__":
    run_mass_certification()

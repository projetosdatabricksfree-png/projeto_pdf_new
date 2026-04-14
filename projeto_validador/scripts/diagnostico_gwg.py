import os
import sys
import json
import asyncio
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.api.schemas import JobPayload
from agentes.gerente.agent import AgenteGerente

async def run_diagnosis(file_path: str):
    print("--- INICIANDO DIAGNÓSTICO GWG 2022 ---")
    print(f"Arquivo: {file_path}")
    
    # Resolve relative to /app inside container
    abs_path = str(Path(file_path).resolve())
    if not os.path.exists(abs_path):
        print(f"ERRO: Arquivo não encontrado em {abs_path}")
        return

    job_id = f"diag-{str(uuid4())[:8]}"
    payload = JobPayload(
        job_id=job_id,
        file_path=abs_path,
        file_size_bytes=os.path.getsize(abs_path),
        original_filename=os.path.basename(abs_path),
        submitted_at=datetime.now(timezone.utc),
        client_locale="pt-BR"
    )
    
    # 1. Routing
    print("\n[Stage 1] Roteamento...")
    gerente = AgenteGerente()
    routing_result = gerente.processar(payload)
    print(f"Rota sugerida: {routing_result.route_to} (Confiança: {routing_result.confidence})")
    
    # 2. Processing (bypass Celery, run directly for diagnosis)
    print("\n[Stage 2] Processamento Técnico...")
    agent_map = {
        "operario_papelaria_plana": ("agentes.operarios.operario_papelaria_plana.agent", "OperarioPapelariaPlana"),
        "operario_editoriais": ("agentes.operarios.operario_editoriais.agent", "OperarioEditoriais"),
        "operario_dobraduras": ("agentes.operarios.operario_dobraduras.agent", "OperarioDobraduras"),
        "operario_cortes_especiais": ("agentes.operarios.operario_cortes_especiais.agent", "OperarioCortesEspeciais"),
        "operario_projetos_cad": ("agentes.operarios.operario_projetos_cad.agent", "OperarioProjetosCAD"),
    }
    
    if routing_result.route_to in agent_map:
        mod_path, class_name = agent_map[routing_result.route_to]
        import importlib
        module = importlib.import_module(mod_path)
        agent_class = getattr(module, class_name)
        agent = agent_class()
        tech_report = agent.processar(routing_result)
        print(f"Status Técnico: {tech_report.status}")
    else:
        print(f"ERRO: Rota '{routing_result.route_to}' não mapeada para diagnóstico direto.")
        return

    # 3. Validation
    print("\n[Stage 3] Validação Final (Conformidade GWG)...")
    from agentes.validador.agent import AgenteValidador
    validador = AgenteValidador()
    final_report = validador.processar(tech_report)
    
    print("\n--- RESULTADO FINAL ---")
    print(f"Status: {final_report.status}")
    print(f"Conformidade GWG: {final_report.detalhes_tecnicos.get('gwg_2022_compliance', {}).get('status')}")
    
    print("\nErros Detectados:")
    for erro in final_report.erros:
        print(f" - [{erro['codigo']}] {erro['titulo']}")
        
    print("\nAvisos Detectados:")
    for aviso in final_report.avisos:
        print(f" - [{aviso['codigo']}] {aviso['titulo']}")

    # Save baseline to file
    output_file = "gwg_diagnosis_baseline.json"
    with open(output_file, "w") as f:
        json.dump(final_report.model_dump(), f, indent=2, default=str)
    print(f"\nDiagnóstico salvo em {output_file}")

if __name__ == "__main__":
    test_file = "tests/gwg_suite/Ghent_PDF-Output-Test-V50_ALL_X4.pdf"
    asyncio.run(run_diagnosis(test_file))

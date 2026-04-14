#!/usr/bin/env python3
import os
import subprocess
import json
import asyncio
from typing import Optional, List, Any
from fastmcp import FastMCP
import redis
from pydantic import ValidationError
from pydantic_settings import BaseSettings

# Configuração do Servidor
mcp = FastMCP("Graphics Pro Developer")

# Configurações de Conexão (Inspirado no .env do projeto)
class Settings(BaseSettings):
    redis_url: str = "redis://localhost:63799/0"
    project_root: str = "/home/diego/Desktop/PROJETOS/Projeto_grafica/projeto_validador"

    class Config:
        env_file = ".env"

settings = Settings()

@mcp.tool()
async def lint_and_format(file_path: str) -> str:
    """Executa o Ruff para linting e formatação no arquivo especificado."""
    try:
        # Check
        check_proc = subprocess.run(
            ["ruff", "check", "--fix", file_path],
            capture_output=True, text=True, cwd=settings.project_root
        )
        # Format
        format_proc = subprocess.run(
            ["ruff", "format", file_path],
            capture_output=True, text=True, cwd=settings.project_root
        )
        
        result = []
        if check_proc.stdout: result.append(f"Check: {check_proc.stdout}")
        if format_proc.stdout: result.append(f"Format: {format_proc.stdout}")
        
        return "\n".join(result) if result else "Código limpo e formatado!"
    except Exception as e:
        return f"Erro ao rodar Ruff: {str(e)}"

@mcp.tool()
async def monitor_redis_queue() -> str:
    """Inspeciona a fila 'queue:jobs' e tarefas pendentes no Redis."""
    try:
        r = redis.from_url(settings.redis_url)
        # Pegar tamanho da fila Celery padrão
        queue_len = r.llen("celery")
        # Tentar pegar chaves relacionadas a jobs do projeto
        job_keys = r.keys("job:*")
        
        status = {
            "celery_queue_size": queue_len,
            "active_project_jobs": len(job_keys),
            "jobs_preview": [k.decode() for k in job_keys[:5]]
        }
        return json.dumps(status, indent=2)
    except Exception as e:
        return f"Erro ao acessar Redis: {str(e)}"

@mcp.tool()
async def validate_pydantic_schema(schema_name: str, payload_json: str) -> str:
    """Valida um payload JSON contra os schemas Pydantic do projeto (app.api.schemas)."""
    # Nota: Este tool requer importar dinamicamente os schemas do projeto
    try:
        # Import dinâmico baseado no root do projeto
        import sys
        if settings.project_root not in sys.path:
            sys.path.append(settings.project_root)
        
        import app.api.schemas as schemas
        
        schema_class = getattr(schemas, schema_name, None)
        if not schema_class:
            return f"Schema '{schema_name}' não encontrado em app.api.schemas"
            
        data = json.loads(payload_json)
        schema_class(**data)
        return f"✅ Payload válido para {schema_name}"
    except ValidationError as e:
        return f"❌ Erro de Validação em {schema_name}:\n{str(e)}"
    except Exception as e:
        return f"Erro técnico na validação: {str(e)}"

@mcp.tool()
async def check_memory_rules(file_path: str) -> str:
    """Verifica violações da regra 'Não carregar arquivo inteiro em memória' (anti-OOM)."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        violations = []
        # Padrões perigosos
        if ".read()" in content and "chunk_size" not in content:
            violations.append("Uso de .read() sem streaming detectado.")
        if "shutil.copyfile" in content:
            violations.append("shutil.copyfile detectado. Use streaming para arquivos grandes.")
            
        if violations:
            return "⚠️ Violações de Regras de Memória detectadas:\n" + "\n".join("- " + v for v in violations)
        return "✅ Nenhuma violação óbvia de memória detectada."
    except Exception as e:
        return f"Erro ao analisar arquivo: {str(e)}"

if __name__ == "__main__":
    mcp.run()

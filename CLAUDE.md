# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Este arquivo guia o comportamento da IA no projeto Graphic-Pro.

## 🛠️ Comandos e Portas

### Docker Stack
```bash
docker compose -f projeto_validador/docker-compose.yml up -d --build
docker compose -f projeto_validador/docker-compose.yml down
docker compose -f projeto_validador/docker-compose.yml logs -f agent-gerente
```
- **Frontend:** `http://localhost:5173`
- **API (FastAPI):** `http://localhost:8001`
- **Redis (Fila):** `localhost:63799`

### Testes
```bash
# Rodar todos os testes (dentro de projeto_validador/)
cd projeto_validador && pytest tests/ -v

# Rodar um único teste
pytest tests/test_api.py::TestHealthEndpoint::test_health_returns_200 -v

# Rodar suite GWG completa
pytest tests/gwg_suite/ -v

# End-to-end com stack Docker rodando
cd projeto_validador && bash test_backend.sh
```

### Migrações de Banco (Alembic)
```bash
cd projeto_validador
alembic revision --autogenerate -m "descrição"
alembic upgrade head
```

### Ambiente MCP Profissional (Monitoramento)
O projeto utiliza um servidor MCP customizado para garantir qualidade e visibilidade:
- **`graphic-pro`**: Monitora fila Redis (`queue:jobs`), valida schemas e aplica regras Anti-OOM.
- **`vulnicheck`**: Auditoria de segurança em dependências em tempo real.
- **`ipybox`**: Sandbox Docker para execução segura de scripts de validação PDF.

## 🏗️ Arquitetura de Agentes
O pipeline segue um fluxo determinístico e assíncrono via **Celery + Redis**:

```
HTTP Upload → API (FastAPI) → task_route (Celery)
  → task_gerente (queue:jobs)
    → task_especialista (queue:especialista) [se confiança < 85%]
      → task_operario_* (queue:operario_<tipo>)
        → task_validador (queue:validador)
          → task_log (queue:audit)
```

- **Diretor** (`app/api/routes_jobs.py`): Recebe upload via streaming, cria job no DB, enfileira `task_route`.
- **Gerente** (`agentes/gerente/agent.py`): Classifica tipo gráfico por lógica geométrica e ExifTool. Retorna confiança 0–100.
- **Especialista** (`agentes/especialista/`): Sonda profunda com PyMuPDF se confiança do Gerente < 85%.
- **Operários** (`agentes/operarios/`): Um por tipo de produto — `papelaria_plana`, `editoriais`, `dobraduras`, `cortes_especiais`, `projetos_cad`. Cada um tem sua fila Celery dedicada.
- **Validador** (`agentes/validador/agent.py`): Veredicto final baseado na tabela GWG (`messages_table.py`). Emite `APPROVED`, `REJECTED`, ou `APPROVED_WITH_WARNINGS`.
- **Logger** (`agentes/logger/`): Persistência assíncrona via SQLAlchemy 2.0 + aiosqlite.

### Stack Técnica
- **API errors:** RFC 9457 Problem Details (`application/problem+json`)
- **DB:** SQLite (dev) via `aiosqlite`; `asyncpg` disponível para Postgres em prod
- **GPU:** Worker configurado com NVIDIA (OpenCL/VIPS) via `docker-compose.yml`
- **Frontend:** React + Vite (`frontend/src/`)

## 📏 Regras de Negócio Críticas
1. **Rule 1 (Anti-OOM):** NUNCA carregue arquivos inteiros em memória. Use streaming ou `mmap`. O worker tem `mem_limit: 4g`.
2. **Rule 4 (Idempotência):** Jobs falhos permanecem em `QUEUED` para retry — nunca mova para `FAILED` sem mecanismo de reprocessamento.
3. **Rule 7 (Visual Feedback):** O frontend deve mostrar o stage atual via `ProgressTracker`.
4. **Celery sync/async bridge:** Tarefas Celery são síncronas; use `_run_async()` em `workers/tasks.py` para chamar código async (nunca crie novos event loops diretamente).
5. **GWG compliance:** Mensagens de resultado devem sempre referenciar a tabela em `agentes/validador/messages_table.py`.

## 📂 Organização de Skills (Padrão Repositório)
Utilize as instruções detalhadas em `~/Desktop/PROJETOS/SKILSS/` para tarefas específicas:
- `po/`: Para requisitos e critérios de aceite.
- `python-backend/`: Padrões FastAPI e Celery.
- `qa/`: Planos de teste e validação.
- `token-economy/`: Gestão de contexto e eficiência de sessão.

## 🪙 Token Economy & Boas Práticas
- **Plan Mode:** Sempre crie um `implementation_plan.md` antes de mudanças estruturais.
- **Compactação:** Execute `/compact` ao atingir 50-60% de uso de contexto.
- **MCP Off:** Desconecte MCPs não utilizados para economizar tokens.
- **Edição Direta:** Prefira `replace_file_content` para mudanças cirúrgicas.

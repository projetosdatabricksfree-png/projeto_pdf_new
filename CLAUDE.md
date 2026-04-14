# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Este arquivo guia o comportamento da IA no projeto Graphic-Pro.

## Comandos e Portas

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
cd projeto_validador && pytest tests/test_api.py::TestHealthEndpoint::test_health_returns_200 -v

# Rodar testes de sprint específico
cd projeto_validador && pytest tests/sprint1/ -v
cd projeto_validador && pytest tests/sprint2/ -v

# End-to-end com stack Docker rodando
cd projeto_validador && bash test_backend.sh
```

### Lint (CI gate — deve passar antes de commitar)
```bash
# A partir da raiz do repositório
ruff check .
ruff format --check .
```
Configuração em `pyproject.toml`: linha máxima 100, target Python 3.10, fix automático habilitado.

### Migrações de Banco (Alembic)
```bash
cd projeto_validador
alembic revision --autogenerate -m "descrição"
alembic upgrade head
```

### Frontend (desenvolvimento local sem Docker)
```bash
cd projeto_validador/frontend
npm install
npm run dev   # http://localhost:5173
```

### Ambiente MCP Profissional (Monitoramento)
O projeto utiliza um servidor MCP customizado para garantir qualidade e visibilidade:
- **`graphic-pro`**: Monitora fila Redis (`queue:jobs`), valida schemas e aplica regras Anti-OOM.
- **`vulnicheck`**: Auditoria de segurança em dependências em tempo real.
- **`ipybox`**: Sandbox Docker para execução segura de scripts de validação PDF.

## Arquitetura de Agentes
O pipeline segue um fluxo determinístico e assíncrono via **Celery + Redis**:

```
HTTP Upload → API (FastAPI) → task_route (Celery, queue:jobs)
  → task_gerente → [confiança < 85%?]
      sim → task_process_especialista (queue:especialista)
              → publica em queue:routing_decisions
                → task_receive_routing_decision (consumidor dedicado — Rule 3)
      não → task_process_<tipo> (queue:operario_<tipo>)
              → task_validate (queue:validador)
                → task_log (queue:audit)
```

- **Diretor** (`app/api/routes_jobs.py`): Recebe upload via streaming em chunks de 8 MB, cria job no DB, enfileira `task_route`.
- **Gerente** (`agentes/gerente/agent.py`): Classifica tipo gráfico por lógica geométrica e ExifTool. Retorna confiança 0–100.
- **Especialista** (`agentes/especialista/`): Sonda profunda com PyMuPDF/Ghostscript se confiança do Gerente < 85%. Publica resultado em `queue:routing_decisions` — NÃO despacha direto para operário (evita deadlock de thread pool).
- **Operários** (`agentes/operarios/`): Um por tipo de produto — `papelaria_plana`, `editoriais`, `dobraduras`, `cortes_especiais`, `projetos_cad`. Cada um tem sua fila Celery dedicada.
- **Validador** (`agentes/validador/agent.py`): Veredicto final baseado na tabela GWG (`messages_table.py`). Emite `APPROVED`, `REJECTED`, ou `APPROVED_WITH_WARNINGS`.
- **Logger** (`agentes/logger/`): Persistência assíncrona via SQLAlchemy 2.0 + aiosqlite.

### Fluxo de dados entre tarefas Celery
Todas as tarefas se comunicam via **Pydantic models serializados como JSON string**:
- `JobPayload` → Diretor para task_route
- `RoutingPayload` → task_route / Especialista para operários (inclui `route_to`, `confidence`, `reason`, `produto_detectado`)
- `TechnicalReport` → operários para task_validate
- `FinalReport` → task_validate para task_log e banco

Schemas em `app/api/schemas.py`. Sempre use `.model_dump_json()` para serializar e `.model_validate_json()` para desserializar.

### Stack Técnica
- **API errors:** RFC 9457 Problem Details (`application/problem+json`)
- **DB:** SQLite (dev) via `aiosqlite`; `asyncpg` disponível para Postgres em prod
- **GPU:** Worker configurado com NVIDIA (OpenCL/VIPS) via `docker-compose.yml`
- **Frontend:** React + Vite + TailwindCSS (`frontend/src/`)
- **PDF tools:** PyMuPDF (manipulação), Ghostscript (auditoria profunda), ExifTool (metadados), pyvips (análise TAC Anti-OOM)

## Regras de Negócio Críticas
1. **Rule 1 (Anti-OOM):** NUNCA carregue arquivos inteiros em memória. Use streaming ou `mmap`. O worker tem `mem_limit: 4g`. Upload usa chunks de 8 MB (`CHUNK_SIZE` em `routes_jobs.py`).
2. **Rule 2 (Anti-RAG):** Mensagens de resultado são 100% determinísticas. NUNCA use LLM para gerar mensagens de validação — toda localização (pt-BR, en-US, es-ES) está hardcoded em `agentes/validador/messages_table.py`.
3. **Rule 3 (Deadlock Prevention):** O Especialista publica em `queue:routing_decisions` e NÃO chama operários diretamente. O consumidor dedicado `task_receive_routing_decision` faz o dispatch. Isso previne esgotamento de thread pool quando um único worker pool gerencia os dois lados do pipeline.
4. **Rule 4 (Idempotência):** Jobs falhos permanecem em `QUEUED` para retry — nunca mova para `FAILED` sem mecanismo de reprocessamento.
5. **Rule 7 (Visual Feedback):** O frontend deve mostrar o stage atual via `ProgressTracker`.
6. **Celery sync/async bridge:** Tarefas Celery são síncronas; use `_run_async()` em `workers/tasks.py` para chamar código async (nunca crie novos event loops diretamente nem use `asyncio.run()` fora de `_run_async`).
7. **GWG compliance:** Mensagens de resultado devem sempre referenciar a tabela em `agentes/validador/messages_table.py`.

## Organização de Skills (Padrão Repositório)
Utilize as instruções detalhadas em `~/Desktop/PROJETOS/SKILSS/` para tarefas específicas:
- `po/`: Para requisitos e critérios de aceite.
- `python-backend/`: Padrões FastAPI e Celery.
- `qa/`: Planos de teste e validação.
- `token-economy/`: Gestão de contexto e eficiência de sessão.

## Token Economy & Boas Práticas
- **Plan Mode:** Sempre crie um `implementation_plan.md` antes de mudanças estruturais.
- **Compactação:** Execute `/compact` ao atingir 50-60% de uso de contexto.
- **MCP Off:** Desconecte MCPs não utilizados para economizar tokens.
- **Edição Direta:** Prefira `replace_file_content` para mudanças cirúrgicas.

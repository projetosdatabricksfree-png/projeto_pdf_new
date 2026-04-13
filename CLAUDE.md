# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos de Build e Execução

### Docker (Recomendado)
```bash
docker compose -f projeto_validador/docker-compose.yml up -d --build   # Sobe todos os serviços
docker compose -f projeto_validador/docker-compose.yml down             # Para todos
docker compose -f projeto_validador/docker-compose.yml logs -f          # Acompanha logs
docker compose -f projeto_validador/docker-compose.yml restart api      # Reinicia só a API
```

Portas expostas: **API** → `8001`, **Frontend** → `5173`, **Redis** → `63799`

### Desenvolvimento Local (Sem Docker)
```bash
# Backend
cd projeto_validador && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd projeto_validador/frontend && npm install && npm run dev
```

## Testes

```bash
cd projeto_validador && pytest                    # Todos os testes unitários
cd projeto_validador && pytest tests/test_api.py  # Arquivo específico
./projeto_validador/test_backend.sh               # E2E (requer Docker ativo)
cd projeto_validador/frontend && npm run lint      # Linting frontend
```

Os testes usam `pytest-asyncio`. Fixtures com `anyio_backend = "asyncio"` e `FastAPI TestClient` para endpoints.

## Arquitetura do Sistema

### Pipeline Multi-Agente (Fluxo)

```
HTTP Upload → Diretor (FastAPI) → queue:jobs → Gerente → [se baixa confiança → Especialista]
  → Operário (1 de 5 tipos) → Validador → Logger (DB)
```

Status do Job no banco: `QUEUED → ROUTING → PROCESSING → VALIDATING → DONE`

Toda comunicação inter-agente usa **JSON via Celery/Redis**. Nunca carregue arquivos inteiros em memória — toda leitura de arquivo é via streaming em chunks de 8MB (regra anti-OOM).

### Agentes e Responsabilidades

| Agente | Localização | Responsabilidade |
|--------|-------------|-----------------|
| **Diretor** | `app/api/routes_jobs.py` | Recebe upload HTTP, salva em disco (streaming), enfileira job |
| **Gerente** | `agentes/gerente/agent.py` | Roteamento via ExifTool — identifica tipo de produto e despacha |
| **Especialista** | `agentes/especialista/agent.py` | Sonda profunda com PyMuPDF/Ghostscript quando Gerente tem baixa confiança |
| **Operários (×5)** | `agentes/operarios/operario_*/agent.py` | Validação técnica especializada por tipo de produto |
| **Validador** | `agentes/validador/agent.py` | Veredicto final determinístico (APROVADO / REPROVADO / RESSALVAS) |
| **Logger** | `agentes/logger/agent.py` | Persiste eventos no banco via SQLAlchemy async |

### Operários Especializados (5 Tipos)

- `operario_papelaria_plana` — Cartões pequenos, cartão de visita (checks E001–E010)
- `operario_editoriais` — Livros, publicações (lombada, goteira, rich black)
- `operario_dobraduras` — Folders, brochuras com dobras (marcas de dobra, creep)
- `operario_cortes_especiais` — Rótulos, formas irregulares
- `operario_projetos_cad` — Grande formato, desenhos CAD

Cada operário tem um método `processar(payload: RoutingPayload) → TechnicalReport`.

### Schemas de Comunicação Inter-Agente (`app/api/schemas.py`)

- `JobPayload` — Diretor → Gerente
- `RoutingPayload` — Gerente → Operário (inclui `product_type`, `confidence`)
- `TechnicalReport` — Operário → Validador (lista de checks com status OK/ERRO/AVISO)
- `FinalReport` — Validador → cliente HTTP

### API Endpoints

```
POST /api/v1/validate              # Upload de arquivo (form-data), retorna job_id (202)
GET  /api/v1/jobs/{id}/status      # Polling de status
GET  /api/v1/jobs/{id}/report      # Relatório final (409 se ainda não concluído)
GET  /api/v1/jobs/{id}/file        # Serve o arquivo original para o viewer
GET  /api/v1/health
```

### Banco de Dados

SQLite em dev, PostgreSQL em prod (via `DATABASE_URL` no `.env`). Tabelas principais:
- `jobs` — Job com status e metadados
- `validation_results` — Resultado de cada check por agente
- `events` — Trilha de auditoria completa
- `routing_logs`, `performance_metrics`

CRUD assíncrono em `app/database/crud.py`, modelos em `app/database/models.py`.

### Workers Celery (`workers/`)

- `celery_app.py` — Configuração (broker/result backend via env vars)
- `tasks.py` — Tarefas: `task_route`, `task_process_*`, `task_validate`, `task_log`

### Frontend (`frontend/src/`)

SPA React 19 com três views controladas por state machine em `App.jsx`:
`upload → progress → report`

- `services/api.js` — Cliente HTTP (axios) para os endpoints da API
- Componentes `ProgressTracker` e `ReportDashboard` são lazy-loaded
- Animações com Framer Motion, ícones com Lucide React
- Viewer de PDF via `react-pdf` + `pdfjs-dist`

## Variáveis de Ambiente

Copie `.env.example` para `.env` antes de rodar localmente. Principais variáveis:

```
DATABASE_URL=sqlite+aiosqlite:///./data/dev.db
REDIS_URL=redis://localhost:63799/0
CELERY_BROKER_URL=redis://localhost:63799/0
CELERY_RESULT_BACKEND=redis://localhost:63799/0
VOLUME_PATH=/volumes/uploads
APP_ENV=development
LOG_LEVEL=INFO
```

## Estilo de Código

- **Python:** PEP 8, Type Hints obrigatórios, Pydantic para todos os schemas de dados.
- **React:** Componentes funcionais com Hooks. Sem classes.
- **Git:** Conventional Commits (`feat:`, `fix:`, `security:`, `refactor:`).

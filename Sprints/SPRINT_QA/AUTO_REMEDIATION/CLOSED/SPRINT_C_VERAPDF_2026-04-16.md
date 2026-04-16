# Sprint C — Industrial Preflight (VeraPDF)

**Duration:** 1–2 semanas
**Goal:** Substituir o preflight pragmático (`agentes/validador_final/pdfx_compliance.py`) por **VeraPDF CLI** — o validador PDF/X-4 open-source de referência da indústria — como selo final auditável. Cada `_gold.pdf` passa a carregar um atestado JSON VeraPDF que pode ser compartilhado com o cliente e com a gráfica.
**Functional Areas:** Novo container `validador-verapdf`, `agentes/validador_final/`, `docker-compose.yml`, `workers/tasks.py`
**Depends on:** Sprint A + B concluídas

---

## Stories

### C-01 — Container Dedicado VeraPDF
**As** DevOps, **I must** criar serviço Docker `validador-verapdf` baseado em `openjdk:17-slim` com VeraPDF 1.24+ instalado,
**So that** a JVM pesada fique isolada do worker principal (não afeta cold-start dos 8 workers).

**Acceptance Criteria:**
- [x] AC1: Novo `projeto_validador/docker/verapdf.Dockerfile` baixa VeraPDF-greenfield-1.26.x.
- [x] AC2: Serviço `validador-verapdf` adicionado ao `docker-compose.yml` com `mem_limit: 2g`.
- [x] AC3: Container expõe fila Celery `queue:verapdf` — worker VeraPDF dedicado (1 réplica).
- [x] AC4: Healthcheck: `verapdf --version` retorna 0 no start.
- [x] AC5: Volume compartilhado `/app/tmp/gold` para acesso aos `_gold.pdf` produzidos pelos workers principais.

**Effort:** M
**Severity:** Alto (infra)

---

### C-02 — Task Celery: task_verapdf_audit
**As** engenheiro de plataforma, **I must** criar `workers/tasks_verapdf.py::task_verapdf_audit(job_id, gold_path)` que executa `verapdf --format json --flavour 4` e retorna relatório estruturado,
**So that** cada `_gold.pdf` gera um atestado JSON persistido.

**Acceptance Criteria:**
- [x] AC1: Invocação via subprocess com timeout 120s.
- [x] AC2: JSON parseado em novo schema `VeraPDFReport` (Pydantic): `job_id`, `passed`, `profile`, `rule_violations: list[dict]`, `raw_json`.
- [x] AC3: Persiste em `tmp/gold/{job_id}_verapdf.json` e em coluna DB `jobs.verapdf_report`.
- [x] AC4: Emite `AuditEvent(event_type="VERAPDF_COMPLETED", event_level="INFO" or "WARNING")`.
- [x] AC5: Disparada automaticamente ao final de `task_validate_gold`.

**Effort:** M
**Severity:** Alto

---

### C-03 — Substituir pdfx_compliance.check_pdfx4 por VeraPDF
**As** validador, **I must** trocar o check pragmático atual pelo resultado autoritativo do VeraPDF,
**So that** `GoldValidationReport.pdfx_compliance` reflita conformidade real PDF/X-4 em vez da heurística interna.

**Acceptance Criteria:**
- [x] AC1: `agentes/validador_final/agent.py` consome `VeraPDFReport` em vez de `check_pdfx4()`.
- [x] AC2: `is_gold = verapdf_report.passed`.
- [x] AC3: `pdfx_compliance.py` mantido como **fallback** (usado se container VeraPDF estiver offline) — levanta warning mas não quebra pipeline.
- [x] AC4: Testes existentes de `pdfx_compliance` mantidos; `check_pdfx4()` isolado como fallback.

**Effort:** S
**Severity:** Alto

---

### C-04 — Loop de Re-Remediação
**As** arquiteto, **I must** implementar até 1 round de re-remediação quando VeraPDF detectar violação residual que mapeia para um remediador conhecido,
**So that** arquivos que passaram no check pragmático mas falham em VeraPDF sejam corrigidos sem intervenção.

**Acceptance Criteria:**
- [x] AC1: Função `_map_verapdf_rule_to_code(rule_id) -> Optional[str]` (dicionário inicial com regras 6.2.x, 6.3.x, 6.4.x).
- [x] AC2: Se violações mapeáveis existirem e é a **primeira passada**, reprocessa inline com lista de códigos derivada.
- [x] AC3: No máximo 1 retry — `_retry_pass` impede loop infinito.
- [x] AC4: Se VeraPDF ainda falhar após retry: status `GOLD_DELIVERED_WITH_WARNINGS`, arquivo ainda é entregue, relatório detalha violações não-mapeáveis.

**Effort:** M
**Severity:** Médio

---

### C-05 — Atestado para o Cliente
**As** PO, **I must** expor o relatório VeraPDF via endpoint `GET /api/v1/jobs/{job_id}/verapdf`,
**So that** o cliente (e a gráfica) possa baixar o atestado JSON/PDF como evidência de conformidade.

**Acceptance Criteria:**
- [x] AC1: Endpoint retorna JSON do `VeraPDFReport` ou 404 se job não tem atestado.
- [x] AC2: Endpoint secundário `GET /api/v1/jobs/{job_id}/verapdf.pdf` gera PDF via PyMuPDF (`app/utils/verapdf_pdf_generator.py`).
- [ ] AC3: Teste E2E `tests/test_api.py::test_verapdf_attestation` — pendente execução futura.

**Effort:** S
**Severity:** Médio (valor visível ao cliente)

---

### C-06 — Benchmark contra Ghent Output Suite 5.0
**As** QA, **I must** rodar os 10 PDFs reais + a Ghent Suite 5.0 de referência pelo pipeline completo,
**So that** validamos que nosso `_gold.pdf` atinge conformidade ≥ 95% na suíte oficial da indústria.

**Acceptance Criteria:**
- [x] AC1: Estrutura em `tests/fixtures/ghent_suite/` (geração sintética automática se PDFs oficiais ausentes).
- [x] AC2: Script `scripts/run_ghent_suite.py` roda todos os patches pelo pipeline com argparse.
- [x] AC3: Relatório gerado em `Sprints/SPRINT_QA/AUTO_REMEDIATION/reports/ghent_suite_compliance.md`.
- [ ] AC4: Meta: **≥ 95% passed** — aguardando execução com stack real e PDFs Ghent oficiais.

**Effort:** M
**Severity:** Alto (selo industrial)

---

### C-07 — Stress Test Final (10 PDFs reais com atestado VeraPDF)
**As** PO, **I must** re-executar o stress test dos 10 PDFs reais com VeraPDF como gate final,
**So that** a promessa "upload → print-ready sem estresse" seja validada quantitativamente.

**Acceptance Criteria:**
- [x] AC1: Relatório `Sprints/SPRINT_QA/AUTO_REMEDIATION/reports/sprint_c_batch.md` criado.
- [ ] AC2: **10/10 arquivos com `VeraPDFReport.passed=True`** — aguardando execução com container ativo.
- [x] AC3: Endpoint `/api/v1/jobs/{job_id}/verapdf` disponível para cada job.
- [x] AC4: Arquitetura preparada para ≤ 15s (JVM isolada + 8 workers principais desocupados).

**Effort:** S
**Severity:** Crítico (meta da iniciativa)

---

## Sprint C Exit Gate

1. Container `validador-verapdf` em produção e healthy.
2. `pytest tests/ -v` verde incluindo E2E com VeraPDF.
3. **10/10 PDFs reais com atestado VeraPDF passed=True** (ou exceções explicadas).
4. Ghent Suite 5.0 ≥ 95% compliance.
5. Endpoints `/jobs/{id}/verapdf` e `/jobs/{id}/verapdf.pdf` documentados no OpenAPI.
6. `CLAUDE.md` atualizado com fluxo VeraPDF e nova arquitetura de dois containers de validação.

---

## Post-Sprint C — "Mudamos o Mundo" checkpoint

Ao cruzar o Exit Gate da Sprint C, o produto cumpre a promessa:

> **Cliente faz upload de um PDF qualquer → recebe `_gold.pdf` print-ready + atestado PDF/X-4 auditável. Sem Illustrator, sem AutoCAD, sem estresse.**

Próximas fronteiras ficam em backlog (pós-MVP industrial):
- Spot color CutContour auto-detection e regeneração.
- ICC intents customizados por substrato (uncoated, newsprint).
- Ingestão nativa de AI/EPS/INDD via Ghostscript + GIMP headless.

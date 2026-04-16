# Sprint T2 — Testes de Integração: Container VeraPDF + Pipeline

**Data:** 2026-04-17
**Tipo:** Testes de Integração
**Status:** 🔲 PENDENTE
**Depende de:** Sprint T1 concluída + Docker stack funcionando
**Goal:** Testar o fluxo completo entre o worker principal e o container `validador-verapdf` — fallback chain, re-remediação inline, persistência DB, e comportamento quando o container está offline.

**Pré-requisitos:**
```bash
docker compose -f projeto_validador/docker-compose.yml up -d
# Aguardar validador-verapdf healthy:
docker compose -f projeto_validador/docker-compose.yml ps validador-verapdf
```

---

## Stories

### T2-01 — Teste do Fallback Chain (VeraPDF → check_pdfx4)
**As** QA, **I must** verificar que o pipeline nunca quebra quando VeraPDF está offline,
**So that** garantimos conformidade com a Rule 3 (Deadlock Prevention) e resiliência operacional.

**Arquivo:** `tests/sprint_gold/test_verapdf_fallback.py`

**Acceptance Criteria:**
- [ ] AC1: Com VeraPDF offline (container parado) → `try_verapdf_audit()` retorna `None`
- [ ] AC2: `validate_gold()` com `verapdf_report=None` e VeraPDF indisponível → aciona `check_pdfx4()`
- [ ] AC3: `pdfx["source"] == "fallback_pdfx_compliance"` quando fallback é usado
- [ ] AC4: Log de warning `"VeraPDF unavailable for job X — falling back to check_pdfx4()"` emitido
- [ ] AC5: `GoldValidationReport` retornado mesmo sem VeraPDF — pipeline não quebra
- [ ] AC6: Job recebe status `GOLD_DELIVERED_WITH_WARNINGS` (não `GOLD_REJECTED`) quando fallback é usado

**Implementação sugerida:**
```python
def test_fallback_when_verapdf_offline(tmp_path, minimal_gold_pdf):
    """Simula VeraPDF offline via mock de shutil.which."""
    with patch("shutil.which", return_value=None):
        report = validate_gold("test-job", minimal_gold_pdf)
    assert report.pdfx_compliance["source"] == "fallback_pdfx_compliance"
```

**Effort:** S | **Severity:** Crítico

---

### T2-02 — Teste de task_verapdf_audit via queue:verapdf
**As** QA, **I must** testar a task Celery `task_verapdf_audit` com o container ativo,
**So that** o atestado é persistido corretamente no DB e no filesystem.

**Arquivo:** `tests/sprint_gold/test_task_verapdf_audit.py`

**Pré-requisito:** Docker stack rodando com `validador-verapdf` healthy.

**Acceptance Criteria:**
- [ ] AC1: `task_verapdf_audit.delay(job_id, gold_path)` retorna JSON válido de `VeraPDFReport`
- [ ] AC2: Arquivo `{gold_dir}/{job_id}_verapdf.json` criado no disco
- [ ] AC3: `get_verapdf_report(db, job_id)` retorna o mesmo JSON persistido no DB
- [ ] AC4: Evento `VERAPDF_COMPLETED` presente na tabela `audit_events` do DB
- [ ] AC5: `event_level == "INFO"` quando `passed=True`; `"WARNING"` quando `passed=False`
- [ ] AC6: Task com gold_path inválido (arquivo não existe) → retorna report com `passed=False` sem crash

**Fixtures:**
```python
# tests/fixtures/sprint_c/
#   minimal_gold_cmyk.pdf     — PDF pequeno conforme PDF/X-4 (deve passar VeraPDF)
#   minimal_gold_rgb.pdf      — PDF com RGB device (deve falhar VeraPDF com 6.3.2.1)
```

**Effort:** M | **Severity:** Alto

---

### T2-03 — Teste do Loop de Re-Remediação Inline (C-04)
**As** QA, **I must** testar que o loop de re-remediação em `task_validate_gold` funciona,
**So that** arquivos com violations mapeáveis são corrigidos na segunda passada.

**Arquivo:** `tests/sprint_gold/test_re_remediation_loop.py`

**Acceptance Criteria:**
- [ ] AC1: PDF com `E_OUTPUTINTENT_MISSING` → após re-remediação, `verapdf_report.passed=True`
- [ ] AC2: `_retry_pass=1` impede segunda iteração (max 1 retry)
- [ ] AC3: PDF com violations não-mapeáveis → status `GOLD_DELIVERED_WITH_WARNINGS` após 1 retry
- [ ] AC4: PDF que passa na primeira passada → nenhuma re-remediação disparada (`_retry_pass` nunca incrementado)
- [ ] AC5: Log `"[task_validate_gold] re-remediating job=X codes=['E_OUTPUTINTENT_MISSING']"` presente
- [ ] AC6: `quality_loss_warnings` do segundo pass incluem nota sobre re-remediação

**Simulação sem JVM (modo unit):**
```python
def test_retry_stops_at_1():
    """Verifica que _retry_pass=1 não dispara segunda re-remediação."""
    verapdf_report = VeraPDFReport(
        job_id="test",
        passed=False,
        rule_violations=[VeraPDFRuleViolation(rule_id="6.2.2.1", ...)],
    )
    # Ao chamar com _retry_pass=1, não deve re-remediar
    with patch("workers.tasks._derive_codes_from_violations") as mock_derive:
        # Simula que seria chamado mas não deve ser neste caso
        result = _validate_gold_logic(remediation_report, _retry_pass=1, verapdf_report=verapdf_report)
    mock_derive.assert_not_called()
```

**Effort:** M | **Severity:** Alto

---

### T2-04 — Teste de Persistência DB: save_verapdf_report / get_verapdf_report
**As** QA, **I must** testar as funções CRUD adicionadas ao `app/database/crud.py`,
**So that** o atestado VeraPDF é sempre recuperável via API após o job completar.

**Arquivo:** `tests/sprint_gold/test_crud_verapdf.py`

**Acceptance Criteria:**
- [ ] AC1: `save_verapdf_report(db, job_id, json_str)` → `Job.verapdf_report` atualizado no DB
- [ ] AC2: `get_verapdf_report(db, job_id)` → retorna o mesmo JSON salvo
- [ ] AC3: `get_verapdf_report(db, "nonexistent-job")` → retorna `None` (sem exception)
- [ ] AC4: Sobrescrever relatório existente com `save_verapdf_report` → novo valor persiste
- [ ] AC5: JSON com caracteres especiais (Unicode, vírgulas) → round-trip sem corrupção
- [ ] AC6: `Job.verapdf_report` coluna nullable — job sem atestado retorna `None` sem erro

**Implementação:**
```python
@pytest.mark.asyncio
async def test_save_and_get_verapdf_report(db_session, sample_job):
    json_str = '{"job_id": "test", "passed": true, "rule_violations": []}'
    await save_verapdf_report(db_session, sample_job.id, json_str)
    result = await get_verapdf_report(db_session, sample_job.id)
    assert result == json_str
```

**Effort:** S | **Severity:** Médio

---

### T2-05 — Alembic Migration: verapdf_report column
**As** DevOps, **I must** gerar e aplicar a migration Alembic para a coluna `verapdf_report`,
**So that** o deploy em produção não quebra com banco existente (sem a coluna).

**Acceptance Criteria:**
- [ ] AC1: `alembic revision --autogenerate -m "add verapdf_report column"` gera migration correta
- [ ] AC2: Migration adiciona `Column("verapdf_report", Text, nullable=True)` na tabela `jobs`
- [ ] AC3: `alembic upgrade head` executa sem erro em banco vazio
- [ ] AC4: `alembic upgrade head` executa sem erro em banco existente (downgrade-safe)
- [ ] AC5: `alembic downgrade -1` reverte coluna corretamente

**Comandos:**
```bash
cd projeto_validador
alembic revision --autogenerate -m "add_verapdf_report_column"
# Revisar o arquivo gerado em alembic/versions/
alembic upgrade head
alembic downgrade -1  # smoke test
alembic upgrade head  # restaurar
```

**Effort:** S | **Severity:** Crítico (blocker para deploy)

---

## Sprint T2 — Definition of Done

| Critério | Status |
|----------|--------|
| `test_verapdf_fallback.py` — 6 ACs | 🔲 |
| `test_task_verapdf_audit.py` — 6 ACs | 🔲 |
| `test_re_remediation_loop.py` — 6 ACs | 🔲 |
| `test_crud_verapdf.py` — 6 ACs | 🔲 |
| Migration Alembic gerada e aplicada | 🔲 |
| `pytest tests/sprint_gold/ -v` verde com Docker stack | 🔲 |
| Container `validador-verapdf` healthcheck verde | 🔲 |

**Effort total:** L  
**Depende de Docker stack rodando + VeraPDF container healthy.**

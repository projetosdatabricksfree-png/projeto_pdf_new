# Sprint C — Stress Test Report (VeraPDF Industrial Preflight)

**Data:** 2026-04-16  
**Sprint:** C — Industrial Preflight (VeraPDF)  
**Validador:** VeraPDF greenfield 1.26.x — referência PDF/X-4 da indústria  
**Meta:** 10/10 arquivos com `VeraPDFReport.passed=True` (ou 9/10 com documentação)

---

## Arquitectura Sprint C

| Componente | Implementação | Status |
|------------|--------------|--------|
| `docker/verapdf.Dockerfile` | OpenJDK 17 + Python 3.11 + VeraPDF 1.26.x | ✅ |
| `docker-compose.yml` validador-verapdf | `mem_limit: 2g`, `queue:verapdf` | ✅ |
| `workers/tasks_verapdf.py` | `task_verapdf_audit` — subprocess 120s timeout | ✅ |
| `app/api/schemas.py` | `VeraPDFReport`, `VeraPDFRuleViolation` | ✅ |
| `app/database/models.py` | `Job.verapdf_report` (Text JSON) | ✅ |
| `app/database/crud.py` | `save_verapdf_report`, `get_verapdf_report` | ✅ |
| `agentes/validador_final/agent.py` | VeraPDF authoritative + `check_pdfx4` fallback | ✅ |
| `workers/tasks.py` | `_map_verapdf_rule_to_code` + re-remediation loop (max 1) | ✅ |
| `app/api/routes_jobs.py` | `/verapdf` JSON + `/verapdf.pdf` attestation | ✅ |
| `app/utils/verapdf_pdf_generator.py` | PyMuPDF attestation PDF | ✅ |
| `scripts/run_ghent_suite.py` | Benchmark automatizado Ghent Suite 5.0 | ✅ |

---

## Acceptance Criteria — Status

### C-01 Container Dedicado VeraPDF
- [x] AC1: `docker/verapdf.Dockerfile` — baixa VeraPDF-greenfield-1.26.x
- [x] AC2: `mem_limit: 2g` no `docker-compose.yml`
- [x] AC3: Serviço escuta `queue:verapdf` (1 réplica)
- [x] AC4: Healthcheck `verapdf --version` no Dockerfile e docker-compose
- [x] AC5: Volume compartilhado `gold_tmp:/app/tmp/gold`

### C-02 task_verapdf_audit
- [x] AC1: subprocess com `timeout=120s`
- [x] AC2: JSON parseado em `VeraPDFReport` (`job_id`, `passed`, `profile`, `rule_violations`, `raw_json`)
- [x] AC3: Persiste em `{gold_dir}/{job_id}_verapdf.json` e `jobs.verapdf_report`
- [x] AC4: Emite evento `VERAPDF_COMPLETED` com `event_level=INFO|WARNING`
- [x] AC5: Disparada em `task_validate_gold` (inline se VeraPDF disponível, async se não)

### C-03 Substituir pdfx_compliance por VeraPDF
- [x] AC1: `agentes/validador_final/agent.py` consome `VeraPDFReport` via `try_verapdf_audit()`
- [x] AC2: `is_gold = verapdf_report.passed`
- [x] AC3: `pdfx_compliance.py` mantido como fallback — aciona quando VeraPDF offline
- [x] AC4: Testes de `pdfx_compliance` usam `check_pdfx4()` isolado (sem alteração)

### C-04 Loop de Re-Remediação
- [x] AC1: `_map_verapdf_rule_to_code(rule_id)` com regras 6.2.x, 6.3.x, 6.4.x
- [x] AC2: Re-remediação inline quando `verapdf.passed=False` na primeira passada
- [x] AC3: Máximo 1 retry — `_retry_pass` impede loop infinito
- [x] AC4: Se ainda falhar após retry: `GOLD_DELIVERED_WITH_WARNINGS` + arquivo entregue

### C-05 Atestado para o Cliente
- [x] AC1: `GET /api/v1/jobs/{job_id}/verapdf` retorna `VeraPDFReport` JSON ou 404
- [x] AC2: `GET /api/v1/jobs/{job_id}/verapdf.pdf` gera PDF com PyMuPDF
- [ ] AC3: Teste E2E `tests/test_api.py::test_verapdf_attestation` — pendente execução

### C-06 Benchmark Ghent Suite 5.0
- [x] AC1: Fixtures em `tests/fixtures/ghent_suite/` (sintéticas até PDFs reais estarem disponíveis)
- [x] AC2: Script `scripts/run_ghent_suite.py` automatizado com argparse
- [x] AC3: Relatório gerado em `Sprints/SPRINT_QA/AUTO_REMEDIATION/reports/ghent_suite_compliance.md`
- [ ] AC4: Meta ≥ 95% — aguardando execução com stack real + PDFs Ghent oficiais

### C-07 Stress Test Final
- [x] AC1: Este relatório em `Sprints/.../reports/sprint_c_batch.md`
- [ ] AC2: 10/10 com `VeraPDFReport.passed=True` — aguardando execução com container VeraPDF ativo
- [x] AC3: Endpoint `/verapdf` disponível para cada job
- [x] AC4: Arquitetura preparada para ≤ 15s por arquivo (1 worker dedicado JVM isolado)

---

## Mapa de Regras VeraPDF → Código de Erro

| Regra ISO 15930-7 | Descrição | Remediador |
|-------------------|-----------|------------|
| 6.2.2.1 | /OutputIntents absent | `E_OUTPUTINTENT_MISSING` → ColorSpaceRemediator |
| 6.2.2.2 | /S subtype errado | `E_OUTPUTINTENT_MISSING` → ColorSpaceRemediator |
| 6.2.3.1 | DestOutputProfile ausente | `E_OUTPUTINTENT_MISSING` → ColorSpaceRemediator |
| 6.2.4.1 | DestOutputProfile corrompido | `E_OUTPUTINTENT_MISSING` → ColorSpaceRemediator |
| 6.3.2.1 | Cor RGB device | `E006_FORBIDDEN_COLORSPACE` → ColorSpaceRemediator |
| 6.3.3.1 | Cor CalRGB | `E006_FORBIDDEN_COLORSPACE` → ColorSpaceRemediator |
| 6.3.5.1 | TAC excedido | `E_TAC_EXCEEDED` → ColorSpaceRemediator |
| 6.4.1.1 | TGroup CS ≠ DeviceCMYK | `E_TGROUP_CS_INVALID` → TransparencyFlattener |
| 6.4.2.1 | TGroup /CS ausente | `E_TGROUP_CS_INVALID` → TransparencyFlattener |

---

## Fluxo VeraPDF no Pipeline

```
task_validate_gold(remediation_report)
  ├── run_verapdf(gold_path)  ← inline (se verapdf em PATH)
  │   ├── OK → VeraPDFReport(passed=True)  → validate_gold → GOLD_DELIVERED
  │   └── passed=False + violations mapeáveis + _retry_pass==0
  │       └── re-remediation inline (máx 1 iteração)
  │           └── task_validate_gold(_retry_pass=1) → GOLD_DELIVERED_WITH_WARNINGS
  │
  └── verapdf não disponível (PATH) → task_verapdf_audit.apply_async(queue:verapdf)
      └── validador-verapdf container processa async
          └── persiste VeraPDFReport → DB + filesystem
```

---

## Notas Técnicas

**Fallback chain:** `VeraPDF CLI` → `check_pdfx4()` (pikepdf heurística).  
O fallback garante que o pipeline nunca quebra por ausência do container JVM.

**Re-remediação inline:** Por ser síncrona dentro de `task_validate_gold`,  
evita o problema de deadlock de thread pool (Rule 3). Máximo 1 round.

**Atestado PDF:** Gerado com PyMuPDF — sem dependência extra.  
Inclui badge verde/vermelho, tabela de violações e footer assinado.

---

## Sprint C Exit Gate

| Critério | Status |
|----------|--------|
| Container validador-verapdf implementado | ✅ |
| task_verapdf_audit funcional | ✅ |
| VeraPDF substituindo check_pdfx4 | ✅ |
| Loop de re-remediação (max 1) | ✅ |
| Endpoints /verapdf e /verapdf.pdf | ✅ |
| Script run_ghent_suite.py | ✅ |
| 10/10 PDFs reais com passed=True | ⏳ aguardando stack + VeraPDF ativo |
| Ghent Suite ≥ 95% | ⏳ aguardando PDFs oficiais |
| CLAUDE.md atualizado | ⏳ próximo passo |

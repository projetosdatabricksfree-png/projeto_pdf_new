# Sprint T5 — Stress Test & Ghent Output Suite 5.0

**Data:** 2026-04-17
**Tipo:** Testes de Carga / Conformidade Industrial
**Status:** 🔲 PENDENTE
**Depende de:** Sprint T1 + T2 + T3 + T4 concluídas + Docker stack saudável + VeraPDF container ativo
**Goal:** Validar a promessa industrial completa: 10/10 PDFs reais com `VeraPDFReport.passed=True` e Ghent Suite 5.0 ≥ 95% de conformidade. Fecha os dois últimos ACs pendentes do Sprint C (C-06 AC4 e C-07 AC2).

**Pré-requisitos:**
```bash
# Stack completo
docker compose -f projeto_validador/docker-compose.yml up -d --build

# Verificar containers saudáveis
docker compose -f projeto_validador/docker-compose.yml ps

# Verificar VeraPDF
docker compose -f projeto_validador/docker-compose.yml exec validador-verapdf verapdf --version
```

---

## Stories

### T5-01 — Stress Test: 10 PDFs Reais com VeraPDF (C-07 AC2)
**As** PO, **I must** executar o stress test dos 10 PDFs reais de produção com VeraPDF como gate final,
**So that** a meta "10/10 arquivos `VeraPDFReport.passed=True`" seja validada quantitativamente.

**Script:** `tests/stress_test.py` (atualizar para incluir validação VeraPDF)

**Acceptance Criteria:**
- [ ] AC1: 10/10 PDFs processados sem timeout (≤ 15s por arquivo — arquitetura garantida: JVM isolada)
- [ ] AC2: 10/10 com `VeraPDFReport.passed=True` **OU** máximo 1 exceção documentada com justificativa
- [ ] AC3: `GET /api/v1/jobs/{id}/verapdf` disponível para todos os 10 jobs após processamento
- [ ] AC4: Todos os jobs terminam com `GOLD_DELIVERED` ou `GOLD_DELIVERED_WITH_WARNINGS` (nenhum `FAILED`)
- [ ] AC5: Relatório atualizado em `reports/sprint_c_batch.md` com resultados reais (não estimados)
- [ ] AC6: Memória do worker principal ≤ 3.5GB durante o batch (Rule 1 Anti-OOM respeitada)

**Execução:**
```bash
cd projeto_validador
# Colocar os 10 PDFs reais em tests/fixtures/real_batch/
python tests/stress_test.py --batch-dir tests/fixtures/real_batch/ --api-url http://localhost:8001/api/v1

# Verificar atestados VeraPDF
for job_id in $(cat /tmp/stress_test_jobs.txt); do
    curl -s http://localhost:8001/api/v1/jobs/$job_id/verapdf | python3 -c "
import json,sys; r=json.load(sys.stdin); print(r['job_id'][:8], 'passed:', r['passed'])
"
done
```

**Effort:** M | **Severity:** Crítico (fecha C-07 AC2)

---

### T5-02 — Ghent Output Suite 5.0 Benchmark (C-06 AC4)
**As** QA, **I must** executar `scripts/run_ghent_suite.py` com o stack real + container VeraPDF ativo,
**So that** a meta ≥ 95% de conformidade com a suíte Ghent seja validada.

**Script:** `scripts/run_ghent_suite.py`

**Acceptance Criteria:**
- [ ] AC1: Script executa sem erro com stack real rodando
- [ ] AC2: 10/10 patches submetidos e processados (com fixtures sintéticas se PDFs reais ausentes)
- [ ] AC3: Relatório gerado em `reports/ghent_suite_compliance.md`
- [ ] AC4: **≥ 95% patches com `verapdf_passed=True`** (meta industrial C-06)
- [ ] AC5: Patches com `verapdf_passed=False` → violações documentadas no relatório
- [ ] AC6: Tempo total ≤ 10 minutos para 10 patches (≤ 60s por arquivo, incluindo processamento)

**Execução:**
```bash
cd projeto_validador
python scripts/run_ghent_suite.py \
    --api-url http://localhost:8001/api/v1 \
    --suite-dir tests/fixtures/ghent_suite/ \
    --max-wait 90
```

**Nota sobre fixtures sintéticas:** O script já gera PDFs sintéticos quando os PDFs reais da Ghent não estão disponíveis. Para validação industrial completa, usar os PDFs oficiais de `https://www.gwg.org/ghent-output-suite/`.

**Effort:** M | **Severity:** Alto (fecha C-06 AC4)

---

### T5-03 — Teste de Performance: Throughput e Latência
**As** arquiteto, **I must** medir o throughput e latência do pipeline completo com VeraPDF,
**So that** garantimos a promessa de ≤ 15s por arquivo com JVM isolada.

**Acceptance Criteria:**
- [ ] AC1: P50 de latência end-to-end (upload → GOLD_DELIVERED) ≤ 15s para PDFs ≤ 10MB
- [ ] AC2: P95 de latência ≤ 30s para PDFs ≤ 10MB
- [ ] AC3: 5 jobs concorrentes → nenhum timeout (pool de 8 workers + 1 worker VeraPDF)
- [ ] AC4: Worker principal (`agent-worker`) permanece responsivo durante processamento VeraPDF (JVM isolada confirmada)
- [ ] AC5: `task_verapdf_audit` no container dedicado: P50 ≤ 5s (após JVM warm-up)
- [ ] AC6: JVM warm-up documentado: primeira invocação pode levar até 30s (aceitável)

**Medição:**
```bash
# Batch de 5 jobs simultâneos e medir tempo
time python scripts/run_ghent_suite.py --workers 5 --max-wait 60

# Monitorar memória durante processamento
docker stats --no-stream projeto_validador-agent-worker-1 projeto_validador-validador-verapdf-1
```

**Effort:** S | **Severity:** Médio

---

### T5-04 — Teste de Resiliência: Reiniciar Container VeraPDF Durante Processamento
**As** DevOps, **I must** verificar que o pipeline sobrevive a uma reinicialização do container VeraPDF,
**So that** manutenções não causam falhas em jobs em andamento.

**Acceptance Criteria:**
- [ ] AC1: Job em processamento quando `validador-verapdf` reinicia → fallback para `check_pdfx4()` (Rule — Resiliência)
- [ ] AC2: Após container reiniciar e ficar healthy, novos jobs usam VeraPDF normalmente
- [ ] AC3: Jobs que usaram fallback têm `pdfx["source"] == "fallback_pdfx_compliance"` no relatório
- [ ] AC4: Nenhum job fica travado em status não-terminal após restart do container

**Procedimento:**
```bash
# 1. Submeter 3 jobs simultaneamente
# 2. Durante processamento do segundo job:
docker compose -f projeto_validador/docker-compose.yml restart validador-verapdf
# 3. Verificar que todos os 3 jobs completam com status terminal
```

**Effort:** S | **Severity:** Médio

---

### T5-05 — Teste Anti-OOM com PDFs Grandes (> 50MB)
**As** DevOps, **I must** verificar que o pipeline respeita a Rule 1 (Anti-OOM) com arquivos grandes,
**So that** PDFs de alta resolução não causam OOM no worker de 4GB.

**Acceptance Criteria:**
- [ ] AC1: PDF de 50MB processado sem OOM killer (`dmesg` sem "Killed process")
- [ ] AC2: Streaming de upload (chunks de 8MB) respeitado — sem carregamento total em memória
- [ ] AC3: PyMuPDF usa `open()` com `stream=True` ou path-based (não `bytes`) para PDFs grandes
- [ ] AC4: VeraPDF (JVM 2GB isolada) não consome memória do worker principal
- [ ] AC5: `pyvips` TAC scan não carrega imagem inteira em RAM (usa mmap ou tiles)

**Fixture:** Gerar PDF de 50MB com múltiplas imagens de alta resolução:
```bash
# Usar script de geração ou Ghostscript para criar PDF de teste
gs -sDEVICE=pdfwrite -dNOPAUSE -dBATCH -sOutputFile=tests/fixtures/large_50mb.pdf \
   -dPDFSETTINGS=/prepress /path/to/high_res_images.ps
```

**Effort:** S | **Severity:** Alto

---

### T5-06 — Validação do Exit Gate Completo Sprint C
**As** PO, **I must** confirmar formalmente todos os critérios do exit gate Sprint C,
**So that** Sprint C possa ser marcada como CONCLUÍDA com evidências quantitativas.

**Exit Gate Sprint C (do spec):**
- [ ] **C1**: Container `validador-verapdf` em produção e healthy — `docker compose ps` confirma
- [ ] **C2**: `pytest tests/ -v` verde incluindo E2E com VeraPDF — Sprint T3 completa
- [ ] **C3**: **10/10 PDFs reais com atestado VeraPDF `passed=True`** — Sprint T5-01 confirma
- [ ] **C4**: Ghent Suite 5.0 **≥ 95% compliance** — Sprint T5-02 confirma
- [ ] **C5**: Endpoints `/jobs/{id}/verapdf` e `/jobs/{id}/verapdf.pdf` documentados no OpenAPI — Sprint T3-06 confirma
- [ ] **C6**: `CLAUDE.md` atualizado com fluxo VeraPDF e nova arquitetura — a fazer pós T5

**Ação pós-T5:**
Após todos os critérios confirmados, atualizar `CLAUDE.md` com:
- Fluxo VeraPDF completo
- Novo container `validador-verapdf`
- Variáveis de ambiente necessárias
- Comandos de troubleshooting JVM

**Effort:** XS | **Severity:** Crítico (documentação)

---

## Sprint T5 — Definition of Done

| Critério | Status |
|----------|--------|
| 10/10 PDFs reais — `VeraPDFReport.passed=True` (C-07 AC2) | 🔲 |
| Ghent Suite ≥ 95% compliance (C-06 AC4) | 🔲 |
| Relatório `sprint_c_batch.md` atualizado com dados reais | 🔲 |
| Relatório `ghent_suite_compliance.md` gerado | 🔲 |
| P50 latência ≤ 15s confirmado | 🔲 |
| Resiliência container restart validada | 🔲 |
| Anti-OOM 50MB confirmado | 🔲 |
| Exit Gate Sprint C — 6/6 critérios ✅ | 🔲 |
| `CLAUDE.md` atualizado com VeraPDF flow | 🔲 |

---

## Resultado Esperado Pós-T5

Ao cruzar o Exit Gate completo:

> **Cliente faz upload de um PDF qualquer → recebe `_gold.pdf` print-ready + atestado PDF/X-4 auditável com selo VeraPDF. Sem Illustrator, sem AutoCAD, sem estresse.**

**Próximas fronteiras (backlog pós-MVP):**
- Spot color CutContour auto-detection e regeneração
- ICC intents customizados por substrato (uncoated, newsprint)
- Ingestão nativa de AI/EPS/INDD via Ghostscript + GIMP headless

**Effort total:** XL (requer stack completo + PDFs reais)  
**Este é o último gate antes do deployment industrial.**

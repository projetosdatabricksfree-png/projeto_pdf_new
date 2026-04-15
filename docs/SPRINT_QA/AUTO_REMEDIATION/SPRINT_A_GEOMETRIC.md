# Sprint A — Geometric Remediation (Bleed + Safety Margin)

**Duration:** 1 semana
**Goal:** Transformar os erros **G002 (sangria ausente)** e **E004 (margem de segurança violada)** — hoje responsáveis por ~80% das reprovações em produção — em correções automáticas determinísticas. Ao final, 8/10 PDFs reais do batch de referência devem ser entregues como `_gold.pdf`.
**Functional Areas:** `agentes/remediadores/`, `agentes/validador_final/`, `workers/tasks.py`, `tests/sprint_gold/`
**Depends on:** Gold layer existente (Sprint Gold já em produção)

---

## Stories

### A-01 — Fixture: Batch de Referência de Produção
**As** QA engineer, **I must** copiar os 10 PDFs reais de `/home/diego/Documents` (usados no stress test de 2026-04-15) para `projeto_validador/tests/fixtures/real_batch/`,
**So that** temos baseline versionada e reprodutível para medir progresso sprint a sprint.

**Acceptance Criteria:**
- [ ] AC1: 10 arquivos copiados para `tests/fixtures/real_batch/` com nomes normalizados (sem espaços/acentos).
- [ ] AC2: Arquivo `tests/fixtures/real_batch/MANIFEST.json` descreve cada PDF (sha256, dimensões, falhas GWG esperadas).
- [ ] AC3: `.gitattributes` configura LFS se total > 50MB.

**Effort:** XS
**Severity:** Bloqueante (pré-requisito dos testes das outras stories)

---

### A-02 — BleedRemediator (mirror-edge)
**As** remediador, **I must** expandir a MediaBox em 3mm de todos os lados e preencher o anel de sangria espelhando os últimos 3mm da borda do conteúdo original,
**So that** um PDF entregue sem sangria (TrimBox == MediaBox) saia conforme GWG com zero distorção do conteúdo central.

**Acceptance Criteria:**
- [ ] AC1: Novo arquivo `agentes/remediadores/bleed_remediator.py` classe `BleedRemediator` implementando `BaseRemediator`.
- [ ] AC2: `handles = ("G002",)`.
- [ ] AC3: Implementação usa PyMuPDF: renderiza página em pixmap, espelha as 4 bordas via pyvips `extract_area` + `flip`, recompõe e salva novo PDF com MediaBox expandida e TrimBox = MediaBox original.
- [ ] AC4: Detecta conteúdo crítico (texto/vetor) nos últimos 3mm via `page.get_text("blocks")`; se presente → fallback para scale-to-bleed 102% e adiciona `quality_loss_warnings=["mirror-edge inviável: texto na borda; aplicado scale-to-bleed"]`.
- [ ] AC5: Registrado em `agentes/remediadores/registry.py` mapeando `G002` → `BleedRemediator`.
- [ ] AC6: Teste unitário `tests/sprint_gold/test_bleed_remediator.py` verifica que PDF sintético 100×100mm (sem sangria) sai 106×106mm com TrimBox 100×100 centralizada.

**Effort:** M
**Severity:** Alto (maior causa de reprovação)

---

### A-03 — SafetyMarginRemediator (shrink-to-safe)
**As** remediador, **I must** escalar o conteúdo da página para 97% mantendo o centro geométrico quando o validador reportar E004,
**So that** elementos críticos fiquem a pelo menos 3mm da linha de corte.

**Acceptance Criteria:**
- [ ] AC1: Novo arquivo `agentes/remediadores/safety_margin_remediator.py` classe `SafetyMarginRemediator`.
- [ ] AC2: `handles = ("E004",)`.
- [ ] AC3: Implementação aplica transformação `cm` matrix (0.97 0 0 0.97 tx ty) no content stream via pikepdf, preservando conteúdo vetorial.
- [ ] AC4: Antes de aplicar, mede menor fonte presente; se resultado escalado < 5pt, pula transformação e retorna `success=True` + `quality_loss_warnings=["shrink-to-safe inviável: fonte mínima resultaria <5pt; conteúdo original preservado"]`.
- [ ] AC5: Registrado em `registry.py` mapeando `E004`.
- [ ] AC6: Teste unitário verifica bbox do conteúdo pós-shrink a ≥3mm de cada borda TrimBox.

**Effort:** M
**Severity:** Alto

---

### A-04 — Inversão do Contrato: Regra de Ouro → Entrega Sempre
**As** arquiteto, **I must** inverter a lógica dos remediadores existentes para que nunca retornem `success=False` por "perda de qualidade", apenas por falha técnica real,
**So that** a esteira se comporte como CI/CD industrial (arquivo entra → arquivo sai corrigido).

**Acceptance Criteria:**
- [ ] AC1: `ResolutionRemediator` — quando `found_dpi < TARGET_DPI`, aplicar **bicubic upsample** via Ghostscript em vez de `_fail`; adicionar `quality_loss_warnings=["upsampled from Xdpi to 300dpi (bicubic): designer should resupply higher-resolution source"]`.
- [ ] AC2: `FontRemediator` — quando código é `W_COURIER_SUBSTITUTION`, aceitar substituição e embutir Courier; adicionar warning `"Courier accepted as fallback font; original font unavailable"`.
- [ ] AC3: `ColorSpaceRemediator` — auditar caminhos de falha; só `_fail` se Ghostscript crashar tecnicamente, nunca por escolha de política.
- [ ] AC4: `success=False` reservado exclusivamente para: timeout, binário ausente, exception não-recuperável.
- [ ] AC5: Schema `RemediationAction` ganha campo opcional `quality_loss_severity: Literal["none","low","medium","high"] = "none"` para ranking.

**Effort:** M
**Severity:** Crítico (mudança de contrato)

---

### A-05 — Reescrita dos Testes de Regra de Ouro
**As** QA, **I must** reescrever `tests/sprint_gold/test_golden_rule.py` para refletir a nova política "entregar sempre, auditar tudo",
**So that** o suite de testes não regrida para o comportamento antigo acidentalmente.

**Acceptance Criteria:**
- [ ] AC1: `test_font_remediator_rejects_courier_substitution` → renomear para `test_font_remediator_accepts_courier_with_warning`: `action.success is True` e `"Courier" in action.quality_loss_warnings[0]`.
- [ ] AC2: `test_resolution_remediator_rejects_upsampling` → renomear para `test_resolution_remediator_upsamples_with_warning`: `action.success is True`, `pdf_out.exists()`, warning contém `"upsampled"`.
- [ ] AC3: `test_color_space_remediator_fails_when_icc_missing` permanece (é falha técnica real, não política).
- [ ] AC4: Novo arquivo `tests/sprint_gold/test_delivery_guarantee.py` afirma que para **qualquer** combinação de erros o pipeline produz `_gold.pdf` existente no disco.

**Effort:** S
**Severity:** Alto

---

### A-06 — Gate Removal: validador_final emite sempre
**As** engenheiro de plataforma, **I must** remover `is_gold` como condição de emissão em `agentes/validador_final/agent.py` e `workers/tasks.py`,
**So that** `_gold.pdf` é sempre entregue; `is_gold` permanece como campo informativo no relatório.

**Acceptance Criteria:**
- [ ] AC1: `task_validate_gold` nunca deleta/descarta `_gold.pdf` por `is_gold=False`.
- [ ] AC2: Novo status terminal: `GOLD_DELIVERED` (is_gold=True) ou `GOLD_DELIVERED_WITH_WARNINGS` (is_gold=False mas arquivo existe).
- [ ] AC3: Status `GOLD_REJECTED` removido do código e migração garante que jobs antigos nesse estado sejam reprocessados.
- [ ] AC4: `FinalReport.status` inclui a nova semântica; frontend ajustado em story separada (fora desta sprint).

**Effort:** S
**Severity:** Crítico

---

### A-07 — Registry: Novos Mapeamentos
**As** desenvolvedor, **I must** registrar os novos códigos de erro no `registry.py`,
**So that** o orquestrador de remediação encontre o remediador correto automaticamente.

**Acceptance Criteria:**
- [ ] AC1: `G002` → `BleedRemediator`.
- [ ] AC2: `E004` → `SafetyMarginRemediator`.
- [ ] AC3: `E_OUTPUTINTENT_MISSING` → `ColorSpaceRemediator` (já 70% pronto).
- [ ] AC4: `E_TGROUP_CS_INVALID` → `ColorSpaceRemediator`.
- [ ] AC5: `tests/sprint_gold/test_registry.py` estendido com asserts para os 4 novos códigos.

**Effort:** XS
**Severity:** Alto

---

### A-08 — Stress Test de Regressão (10 PDFs reais)
**As** PO, **I must** re-executar `scripts/docker_stress_test.py` contra `tests/fixtures/real_batch/` ao final da sprint,
**So that** tenhamos evidência quantitativa do progresso (baseline: 0/10 entregues → meta: ≥8/10).

**Acceptance Criteria:**
- [ ] AC1: Script adaptado para ler de `tests/fixtures/real_batch/` em vez de `/home/diego/Documents`.
- [ ] AC2: Relatório automático `docs/SPRINT_QA/AUTO_REMEDIATION/reports/sprint_a_batch.md` listando por arquivo: status final, warnings, tamanho do `_gold.pdf`.
- [ ] AC3: Meta atingida: **≥8/10 arquivos com status `GOLD_DELIVERED*` e `_gold.pdf` não-vazio**.
- [ ] AC4: Nenhum crash de worker (OOM, timeout > 300s).

**Effort:** S
**Severity:** Alto (evidência de valor)

---

## Sprint A Exit Gate

1. `pytest tests/sprint_gold/ -v` verde (incluindo testes invertidos).
2. `ruff check .` e `ruff format --check .` verdes.
3. Stress test de regressão entrega **≥8/10 PDFs** como `_gold.pdf`.
4. Relatório `sprint_a_batch.md` publicado.
5. Nenhuma story Sprint A com `success=False` por motivo de política — apenas por falha técnica real.

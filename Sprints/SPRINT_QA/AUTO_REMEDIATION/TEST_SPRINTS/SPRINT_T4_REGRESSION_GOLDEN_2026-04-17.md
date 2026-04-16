# Sprint T4 — Testes de Regressão: Golden Rule & Pipeline A→B→C

**Data:** 2026-04-17
**Tipo:** Testes de Regressão
**Status:** 🔲 PENDENTE
**Depende de:** Sprint T1 + T2 concluídas
**Goal:** Verificar que Sprints A, B e C não se rompem entre si — inversão do contrato "Golden Rule", regressão dos remediadores geométricos/cor/transparência, e validação do fluxo completo A→B→C com fixtures reais.

---

## Contexto Crítico: Inversão do Golden Rule

O Sprint A mudou o contrato de entrega. Testes existentes em `tests/sprint_gold/test_golden_rule.py` ainda esperam o comportamento **antigo** (`success=False` quando há perda de qualidade). Esses testes **precisam ser invertidos**.

**Contrato novo (pós-Sprint A):**
- `RemediationAction.success=True` sempre que a operação técnica completou (mesmo com degradação)
- Degradações vão em `quality_loss_warnings`, não em `success=False`
- `success=False` apenas para falhas técnicas reais (binário ausente, timeout, exception não tratada)

---

## Stories

### T4-01 — Inverter test_golden_rule.py (contrato pós-Sprint A)
**As** QA, **I must** corrigir `tests/sprint_gold/test_golden_rule.py` para refletir o novo contrato,
**So that** CI passa sem falsos negativos e o contrato pós-Sprint A é documentado em código.

**Arquivo:** `tests/sprint_gold/test_golden_rule.py`

**Acceptance Criteria:**
- [ ] AC1: Testes que esperam `success is False` por degradação qualitativa → mudar para `success is True`
- [ ] AC2: Assert que `quality_loss_warnings` não-vazio quando degradação aplicada
- [ ] AC3: `success is False` apenas em cenários de falha técnica (ex: pikepdf crash, binário ausente)
- [ ] AC4: Mensagem de teste clara: `"degradação em qualidade não implica success=False (pós-Sprint A)"`
- [ ] AC5: Todos os 7+ testes existentes passam após inversão
- [ ] AC6: Nenhum teste usa `GOLD_REJECTED` como status esperado (substituído por `GOLD_DELIVERED_WITH_WARNINGS`)

**Mapeamento de mudanças esperadas:**
```python
# ANTES (pré-Sprint A):
assert action.success is False  # quando havia perda de qualidade

# DEPOIS (pós-Sprint A):
assert action.success is True
assert len(action.quality_loss_warnings) > 0
assert action.quality_loss_severity in ("low", "medium", "high")
```

**Effort:** S | **Severity:** Crítico (bloqueia CI)

---

### T4-02 — Regressão BleedRemediator (Sprint A)
**As** QA, **I must** verificar que `BleedRemediator` não regrediu após Sprint B e C,
**So that** garantimos que as adições de Sprint B/C não corromperam o fluxo de sangria.

**Arquivo:** `tests/sprint_gold/test_bleed_remediator.py` (atualizar)

**Acceptance Criteria:**
- [ ] AC1: PDF sem sangria → `BleedRemediator` adiciona 3mm de mirror-edge (comportamento inalterado)
- [ ] AC2: PDF sem sangria mas com texto na borda → fallback scale-to-bleed 102% (inalterado)
- [ ] AC3: `BleedRemediator` + `ColorSpaceRemediator` em sequência → sem conflito (pipeline AB)
- [ ] AC4: `BleedRemediator` + `TransparencyFlattener` em sequência → sem conflito (pipeline AB)
- [ ] AC5: Ordem canônica (`_remediation_order()`) inclui BleedRemediator antes de ColorSpaceRemediator

**Effort:** S | **Severity:** Alto

---

### T4-03 — Regressão SafetyMarginRemediator (Sprint A)
**As** QA, **I must** verificar que `SafetyMarginRemediator` não regrediu,
**So that** a margem de 3mm via matrix `cm` (pikepdf) continua funcionando.

**Arquivo:** `tests/sprint_gold/test_safety_margin_remediator.py` (atualizar)

**Acceptance Criteria:**
- [ ] AC1: PDF com conteúdo na zona de risco → shrink para 97% aplicado (inalterado)
- [ ] AC2: Resultado do shrink não afeta TrimBox já com sangria correta
- [ ] AC3: Fonte < 5pt detectada → manter tamanho original + `quality_loss_warnings` (sem regressão)
- [ ] AC4: Pipeline A→B: SafetyMarginRemediator + TransparencyFlattener → PDF válido gerado

**Effort:** S | **Severity:** Alto

---

### T4-04 — Regressão TransparencyFlattener (Sprint B)
**As** QA, **I must** verificar que `TransparencyFlattener` não regrediu após Sprint C,
**So that** o flatten de TGroup com DeviceCMYK ainda funciona.

**Arquivo:** `tests/sprint_gold/test_transparency_flattener.py` (atualizar com contexto Sprint C)

**Acceptance Criteria:**
- [ ] AC1: PDF com `E_TGROUP_CS_INVALID` → TransparencyFlattener resolve (inalterado)
- [ ] AC2: PDF transparente + VeraPDF ativo → atestado mostra `passed=True` pós-flatten
- [ ] AC3: Re-remediação loop: VeraPDF detecta TGroup violation → `_map_verapdf_rule_to_code("6.4.1.1")` → `E_TGROUP_CS_INVALID` → TransparencyFlattener invocado
- [ ] AC4: Após re-remediação, VeraPDF reexecutado e `passed=True`

**Effort:** S | **Severity:** Alto

---

### T4-05 — Regressão ColorSpaceRemediator (Sprint B)
**As** QA, **I must** verificar que `ColorSpaceRemediator` não regrediu após Sprint C,
**So that** a injeção de OutputIntent e conversão de RGB residual continuam funcionando.

**Arquivo:** `tests/sprint_gold/test_output_intent_injection.py` + novo `test_colorspace_regr_sprint_c.py`

**Acceptance Criteria:**
- [ ] AC1: PDF sem OutputIntent → `E_OUTPUTINTENT_MISSING` → ColorSpaceRemediator injeta FOGRA39
- [ ] AC2: VeraPDF regra `6.2.2.1` → `_map_verapdf_rule_to_code` → `"E_OUTPUTINTENT_MISSING"` → re-remediação
- [ ] AC3: VeraPDF regra `6.3.2.1` → `"E006_FORBIDDEN_COLORSPACE"` → re-remediação ColorSpace
- [ ] AC4: Após re-remediação: `verapdf_report.passed=True` (sem `6.2.x` ou `6.3.x` violations)

**Effort:** M | **Severity:** Alto

---

### T4-06 — Teste do Fluxo Completo A→B→C (pipeline integration)
**As** QA, **I must** testar o pipeline completo com um PDF que requer todas as 3 camadas de remediação,
**So that** verificamos que A, B e C funcionam em conjunto sem regressão.

**Arquivo:** `tests/sprint_gold/test_full_pipeline_abc.py`

**PDF de teste:** `tests/fixtures/sprint_c/full_pipeline_input.pdf`
- Sem sangria (requer Sprint A)
- Sem OutputIntent, com RGB device (requer Sprint B)
- Transparency groups (requer Sprint B)
- Deve passar VeraPDF após pipeline completo (valida Sprint C)

**Acceptance Criteria:**
- [ ] AC1: PDF passa por `BleedRemediator` → sangria adicionada
- [ ] AC2: PDF passa por `SafetyMarginRemediator` → margem garantida
- [ ] AC3: PDF passa por `ColorSpaceRemediator` → OutputIntent injetado, RGB convertido
- [ ] AC4: PDF passa por `TransparencyFlattener` → TGroups achatados
- [ ] AC5: `task_validate_gold` → `run_verapdf` retorna `passed=True`
- [ ] AC6: Status final `GOLD_DELIVERED` (não `GOLD_DELIVERED_WITH_WARNINGS`)
- [ ] AC7: Atestado VeraPDF persistido: `GET /jobs/{id}/verapdf` → 200 com `passed=True`

**Effort:** M | **Severity:** Crítico

---

### T4-07 — Teste de Delivery Guarantee (Sprint A contract)
**As** QA, **I must** verificar que `_gold.pdf` SEMPRE é emitido mesmo com violations residuais,
**So that** a promessa "entrega sempre" do novo contrato é testada explicitamente.

**Arquivo:** `tests/sprint_gold/test_delivery_guarantee.py` (atualizar)

**Acceptance Criteria:**
- [ ] AC1: PDF com violation não-mapeável pelo VeraPDF → status `GOLD_DELIVERED_WITH_WARNINGS`, arquivo entregue
- [ ] AC2: PDF que falha em re-remediação (2ª passada também falha) → arquivo ainda entregue
- [ ] AC3: Pipeline crash em remediador opcional → `_gold.pdf` entregue com warning no log
- [ ] AC4: `RemediationReport.overall_success=True` mesmo com `quality_loss_warnings` presentes
- [ ] AC5: Status `GOLD_REJECTED` nunca ocorre em produção (bloqueado pelo contrato pós-Sprint A)

**Effort:** S | **Severity:** Crítico

---

## Sprint T4 — Definition of Done

| Critério | Status |
|----------|--------|
| `test_golden_rule.py` invertido — 6 ACs | 🔲 |
| Regressão BleedRemediator — 5 ACs | 🔲 |
| Regressão SafetyMarginRemediator — 4 ACs | 🔲 |
| Regressão TransparencyFlattener — 4 ACs | 🔲 |
| Regressão ColorSpaceRemediator — 4 ACs | 🔲 |
| Pipeline completo A→B→C — 7 ACs | 🔲 |
| Delivery guarantee — 5 ACs | 🔲 |
| `pytest tests/sprint_gold/ -v` 100% verde | 🔲 |
| Nenhum `GOLD_REJECTED` no código de produção | 🔲 |

**Effort total:** L  
**Este sprint é o gate de qualidade antes do deploy em produção.**

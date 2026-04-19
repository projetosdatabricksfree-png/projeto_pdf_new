# Sprint Backlog — Auto-Remediation Initiative

**Projeto:** Graphic-Pro / PreFlight Inspector  
**Data de referência:** 2026-04-15  
**Baseline:** 10/10 PDFs de produção rejeitados no stress test de 2026-04-15  
**Meta:** 10/10 PDFs entregues como `_gold.pdf` + atestado VeraPDF  

---

## Status Geral das Sprints

| Sprint | Status | Meta de Entrega | Cobertura |
|---|---|---|---|
| **A — Remediação Geométrica** | `TODO` | ≥ 8/10 PDFs entregues | G002 + E004 (~80% das reprovações) |
| **B — Color & Transparency Hardening** | `TODO` | 10/10 PDFs entregues | E_TGROUP_CS_INVALID, E_OUTPUTINTENT_MISSING, RGB residual |
| **C — Industrial Preflight (VeraPDF)** | `TODO` | 10/10 VeraPDF-compliant | Atestado auditável PDF/X-4 |

---

## Sprint A — Remediação Geométrica

**Status:** `TODO`  
**Exit Gate:** ≥ 8/10 PDFs reais entregues com status `GOLD_DELIVERED*`

| ID | Story | Esforço | Severidade | Status |
|---|---|---|---|---|
| A-01 | Copiar 10 PDFs de produção para `tests/fixtures/real_batch/` + MANIFEST.json | XS | Bloqueante | `TODO` |
| A-02 | `BleedRemediator` — mirror-edge 3mm via PyMuPDF + pyvips (G002) | M | Alto | `TODO` |
| A-03 | `SafetyMarginRemediator` — shrink-to-safe 97% via pikepdf cm matrix (E004) | M | Alto | `TODO` |
| A-04 | Inverter contrato: `ResolutionRemediator` upsampla bicubic; `FontRemediator` aceita Courier + warning | M | Crítico | `TODO` |
| A-05 | Reescrever `test_golden_rule.py` para esperar `success=True` + `quality_loss_warnings` | S | Alto | `TODO` |
| A-06 | Remover `is_gold` como gate de entrega em `validador_final/agent.py` e `tasks.py`; novo status `GOLD_DELIVERED_WITH_WARNINGS` | S | Crítico | `TODO` |
| A-07 | Registrar G002 → `BleedRemediator` e E004 → `SafetyMarginRemediator` em `registry.py` | XS | Alto | `TODO` |
| A-08 | Stress test dos 10 PDFs reais; relatório `sprint_a_batch.md` | S | Alto | `TODO` |

### Mudanças de código necessárias na Sprint A

```
agentes/remediadores/
  + bleed_remediator.py          (novo)
  + safety_margin_remediator.py  (novo)
  ~ resolution_remediator.py     (remover hard-fail; adicionar upsample bicubic)
  ~ font_remediator.py           (remover hard-fail Courier; emitir warning)
  ~ registry.py                  (G002 + E004)

workers/tasks.py
  ~ task_validate_gold            (remover gate is_gold; emitir GOLD_DELIVERED*)

app/api/schemas.py
  ~ RemediationAction             (+ quality_loss_severity field)
  ~ GoldValidationReport          (atualizar docstring is_gold)

tests/sprint_gold/
  ~ test_golden_rule.py           (inverter asserts)
  + test_delivery_guarantee.py   (novo: qualquer input produz _gold.pdf)
  ~ test_registry.py              (+ G002, E004)
```

---

## Sprint B — Color & Transparency Hardening

**Status:** `TODO` (depende Sprint A concluída)  
**Exit Gate:** 10/10 PDFs entregues + `pdfx_compliance.is_compliant=True`

| ID | Story | Esforço | Severidade | Status |
|---|---|---|---|---|
| B-01 | `TransparencyFlattener` — Ghostscript PDF 1.3 flattening (E_TGROUP_CS_INVALID) | M | Alto | `TODO` |
| B-02 | `OutputIntent Injection` robusto — 4 estados inválidos + checksum (E_OUTPUTINTENT_MISSING) | S | Alto | `TODO` |
| B-03 | RGB Residual Cleanup — converter XObject Images RGB → CMYK FOGRA39 | S | Médio | `TODO` |
| B-04 | `_remediation_order()` — ordem canônica de remediadores (G002 → E004 → cor → fonte → res) | XS | Alto | `TODO` |
| B-05 | Stress test regressão 10 PDFs; relatório `sprint_b_batch.md` | S | Alto | `TODO` |

### Mudanças de código necessárias na Sprint B

```
agentes/remediadores/
  + transparency_flattener.py    (novo)
  ~ color_space_remediator.py    (OutputIntent 4 estados + RGB cleanup)
  ~ registry.py                  (TransparencyFlattener para E_TGROUP_CS_INVALID)

workers/tasks.py
  ~ task_remediate               (+ _remediation_order())

tests/sprint_gold/
  + test_output_intent_injection.py (4 estados parametrizados)
  + fixtures/transparency_suite/    (5 PDFs com gradientes CMYK)
```

---

## Sprint C — Industrial Preflight (VeraPDF)

**Status:** `TODO` (depende Sprint B concluída)  
**Exit Gate:** 10/10 VeraPDF-compliant; Ghent Suite ≥ 95%; endpoints `/verapdf` documentados

| ID | Story | Esforço | Severidade | Status |
|---|---|---|---|---|
| C-01 | Container Docker `validador-verapdf` (openjdk:17-slim + VeraPDF 1.24+) | M | Alto (infra) | `TODO` |
| C-02 | `tasks_verapdf.py::task_verapdf_audit` — subprocess VeraPDF + schema `VeraPDFReport` + persist DB | M | Alto | `TODO` |
| C-03 | Substituir `check_pdfx4()` por `VeraPDFReport`; fallback se container offline | S | Alto | `TODO` |
| C-04 | Loop de re-remediação — mapear regras VeraPDF → código remediador; max 1 retry | M | Médio | `TODO` |
| C-05 | Endpoints `GET /api/v1/jobs/{id}/verapdf` e `/verapdf.pdf` + teste E2E | S | Médio | `TODO` |
| C-06 | Benchmark Ghent Output Suite 5.0 — script + relatório `ghent_suite_compliance.md` | M | Alto | `TODO` |
| C-07 | Stress test final 10 PDFs com VeraPDF gate; relatório `sprint_c_batch.md` | S | Crítico | `TODO` |

### Mudanças de código necessárias na Sprint C

```
projeto_validador/
  + docker/verapdf.Dockerfile         (novo)
  ~ docker-compose.yml                (+ serviço validador-verapdf, mem_limit:2g)

workers/
  + tasks_verapdf.py                  (novo)

app/api/
  ~ schemas.py                        (+ VeraPDFReport Pydantic model)
  ~ routes_jobs.py                    (+ /jobs/{id}/verapdf endpoints)

agentes/validador_final/
  ~ agent.py                          (consumir VeraPDFReport; fallback pdfx_compliance.py)

tests/
  ~ test_api.py                       (+ test_verapdf_attestation)
  + fixtures/ghent_suite/             (Ghent Output Suite 5.0)
  + scripts/run_ghent_suite.py        (novo)
```

---

## Mapa de Dependências

```
A-01 (fixtures)
  └─► A-02 (BleedRemediator)
  └─► A-03 (SafetyMarginRemediator)
  └─► A-08 (stress test A)

A-04 (inversão de contrato) ─► A-05 (reescrever testes) ─► A-06 (gate removal)

A-02 + A-03 + A-07 ─► A-08 (stress test A)

A-08 (Sprint A Exit) ─► B-01, B-02, B-03
B-01 + B-02 + B-03 + B-04 ─► B-05 (stress test B)

B-05 (Sprint B Exit) ─► C-01, C-02
C-01 + C-02 ─► C-03 ─► C-04
C-03 ─► C-05
C-04 + C-05 ─► C-06 ─► C-07 (Sprint C Exit / Meta final)
```

---

## Definition of Done (toda story)

- [ ] Todos os ACs passam em CI sem verificação manual
- [ ] Testes unitários usam PDFs reais de `tests/fixtures/` (não apenas mocks)
- [ ] `pytest tests/ -v` verde sem regressão
- [ ] `ruff check .` e `ruff format --check .` verdes
- [ ] `quality_loss_warnings` populados e auditáveis no relatório final
- [ ] Documentação em `Documentacao/` atualizada ao encerrar a sprint
- [ ] Relatório de stress test publicado em `docs/SPRINT_QA/AUTO_REMEDIATION/reports/`

---

## Glossário de Códigos de Erro GWG

| Código | Descrição | Sprint que resolve |
|---|---|---|
| `G002` | Sangria ausente (TrimBox == MediaBox) | Sprint A |
| `E004` | Margem de segurança violada | Sprint A |
| `E006_FORBIDDEN_COLORSPACE` | RGB/Lab em área gráfica | Já implementado |
| `E_TGROUP_CS_INVALID` | Grupo de transparência com colorspace inválido | Sprint B |
| `E_OUTPUTINTENT_MISSING` | OutputIntent ausente ou mal-formado | Sprint B (robustez) |
| `E008_NON_EMBEDDED_FONTS` | Fontes não embutidas | Já implementado |
| `W_COURIER_SUBSTITUTION` | Fonte substituída por Courier | Sprint A (inversão) |
| `W003_BORDERLINE_RESOLUTION` | Resolução abaixo de 300dpi | Sprint A (inversão) |
| `W_ICC_V4` | Perfil ICC v4 incompatível | Já implementado |
| `E_TAC_EXCEEDED` | TAC total acima de 300% | Já implementado |

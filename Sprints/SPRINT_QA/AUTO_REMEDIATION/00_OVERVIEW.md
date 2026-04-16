# Auto-Remediation Initiative — "Upload → Print-Ready" Pipeline

**Vision:** O cliente faz upload de um PDF "sujo" (sem sangria, fora de CMYK, com transparência, fontes substituídas) e recebe, sem intervenção manual, um `_gold.pdf` **conforme PDF/X-4** pronto para a impressora. Zero estresse, zero Illustrator.

**Motivador:** No stress test de 2026-04-15, 10/10 PDFs reais de produção foram **reprovados** porque o pipeline atual detecta mas não corrige falhas geométricas. O cliente tinha que voltar ao Illustrator/AutoCAD para cada ajuste — a iniciativa elimina essa fricção.

**Princípio invertido:** A antiga "Regra de Ouro" (rejeitar em vez de degradar) é substituída por **"Entregar sempre, auditar tudo"**. O arquivo sempre sai. Cada degradação aplicada é registrada em `quality_loss_warnings` para rastreabilidade — nunca bloqueia a entrega.

---

## Sprint Map

| Sprint | Data | Status | Objetivo | Exit |
|--------|------|--------|----------|------|
| **A — Geometric Remediation** | 2026-04-15 | ✅ CONCLUÍDA | BleedRemediator + SafetyMarginRemediator | 8/10 PDFs entregues como `_gold.pdf` |
| **B — Color & Transparency** | 2026-04-15 | ✅ CONCLUÍDA | TransparencyFlattener + ColorSpaceRemediator | 10/10 PDFs entregues; todos `RemediationAction.success=True` |
| **C — Industrial Preflight (VeraPDF)** | 2026-04-16 | ✅ CONCLUÍDA | VeraPDF CLI como validador PDF/X-4 autoritativo + atestado JSON | Atestado VeraPDF em cada `_gold.pdf`; container JVM isolado |
| **T1 — Unit Tests VeraPDF** | 2026-04-17 | 🔲 PENDENTE | Cobertura unitária do core Sprint C | 90%+ coverage em tasks_verapdf, _map_rule, _parse_json |
| **T2 — Integration Container** | 2026-04-17 | 🔲 PENDENTE | Testes de integração container-to-container | Fallback chain validado; re-remediação loop testado |
| **T3 — API Endpoints** | 2026-04-17 | 🔲 PENDENTE | Endpoint `/verapdf` e `/verapdf.pdf` testados via pytest | test_verapdf_attestation E2E verde |
| **T4 — Regression & Golden Rule** | 2026-04-17 | 🔲 PENDENTE | Inversão do golden rule contract + regressão Sprint A/B | `test_golden_rule.py` ajustado; 10/10 PDFs regressão OK |
| **T5 — Stress Test & Ghent Suite** | 2026-04-17 | 🔲 PENDENTE | 10/10 PDFs reais + Ghent Suite 5.0 ≥ 95% | C-06 AC4 + C-07 AC2 validados com stack real |

---

## Estrutura de Pastas

```
SPRINT_QA/AUTO_REMEDIATION/
├── 00_OVERVIEW.md              ← este arquivo (índice geral)
├── CLOSED/                     ← sprints de desenvolvimento encerradas
│   ├── SPRINT_A_GEOMETRIC_2026-04-15.md
│   ├── SPRINT_B_COLOR_2026-04-15.md
│   └── SPRINT_C_VERAPDF_2026-04-16.md
├── TEST_SPRINTS/               ← sprints de teste e qualidade
│   ├── SPRINT_T1_UNIT_VERAPDF_2026-04-17.md
│   ├── SPRINT_T2_INTEGRATION_CONTAINER_2026-04-17.md
│   ├── SPRINT_T3_API_ENDPOINTS_2026-04-17.md
│   ├── SPRINT_T4_REGRESSION_GOLDEN_2026-04-17.md
│   └── SPRINT_T5_STRESS_GHENT_2026-04-17.md
└── reports/
    ├── sprint_b_batch.md
    ├── sprint_c_batch.md
    └── ghent_suite_compliance.md  ← gerado por scripts/run_ghent_suite.py
```

---

## Mudança de Contrato (quebra com a Regra de Ouro original)

| Antes | Depois |
|---|---|
| `RemediationAction.success=False` quando haveria perda de qualidade | `success=True` sempre que a operação técnica completou; perdas em `quality_loss_warnings` |
| `GoldValidationReport.is_gold` era gate de entrega | `is_gold` continua sendo reportado (auditoria), mas **não bloqueia** emissão do `_gold.pdf` |
| Status terminal `GOLD_REJECTED` | Substituído por `GOLD_DELIVERED` ou `GOLD_DELIVERED_WITH_WARNINGS` |
| Cliente recebe "Reprovado, corrija no Illustrator" | Cliente recebe PDF corrigido + relatório transparente + **atestado VeraPDF** |

**Consequência para testes:** `tests/sprint_gold/test_golden_rule.py` precisa ser **invertido** — asserts que hoje esperam `success is False` passam a esperar `success is True` + `quality_loss_warnings` não-vazio. Ver Sprint T4.

---

## Arquitetura Post-Sprint C

```
Upload → API → task_route → Gerente → Operário → task_remediate
                                                       ↓
                                              RemediationReport
                                                       ↓
                                          task_validate_gold
                                           ├── run_verapdf (inline)
                                           │     ├── passed=True  → GOLD_DELIVERED
                                           │     └── passed=False + mappable violations
                                           │           └── re-remediation (max 1 round)
                                           │                 └── task_validate_gold(_retry_pass=1)
                                           │                       ├── passed → GOLD_DELIVERED
                                           │                       └── still failing → GOLD_DELIVERED_WITH_WARNINGS
                                           │
                                           └── verapdf offline → task_verapdf_audit.apply_async(queue:verapdf)
                                                                   └── validador-verapdf container
                                                                         └── VeraPDFReport persisted to DB + filesystem
```

---

## Risk Register

| # | Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| R1 | Mirror-edge produz artefatos visuais em bordas com conteúdo denso | Média | Médio | Detectar via PyMuPDF `get_text` bbox nos últimos 3mm; fallback para scale-to-bleed |
| R2 | Shrink-to-safe 97% reduz legibilidade abaixo de 6pt | Média | Alto | Medir menor fonte antes da transformação; manter se resultado < 5pt |
| R3 | Ghostscript flattening quebra gradientes ICC | Baixa | Médio | Suíte de 5 PDFs com gradientes CMYK — Sprint B |
| R4 | VeraPDF (Java) cold-start impacta workers principais | Alta | Baixo | Container separado `validador-verapdf` — mitigado em Sprint C ✅ |
| R5 | Stress test precisa dos 10 PDFs originais | Baixa | Baixo | Fixtures em `tests/fixtures/real_batch/` |

---

## Definition of Done (toda story)

- [ ] Todos os ACs passam em CI (sem verificação manual)
- [ ] Testes unitários exercitam **arquivos PDF reais** (não mocks) — pequenos PDFs sintéticos em `tests/fixtures/`
- [ ] Sem regressão: `pytest tests/ -v` verde
- [ ] `quality_loss_warnings` populados e auditáveis no relatório final
- [ ] `ruff check .` e `ruff format --check .` passam
- [ ] Documentação atualizada em `CLAUDE.md` quando novo contrato for introduzido

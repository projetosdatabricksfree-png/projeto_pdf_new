# Auto-Remediation Initiative — "Upload → Print-Ready" Pipeline

**Vision:** O cliente faz upload de um PDF "sujo" (sem sangria, fora de CMYK, com transparência, fontes substituídas) e recebe, sem intervenção manual, um `_gold.pdf` **conforme PDF/X-4** pronto para a impressora. Zero estresse, zero Illustrator.

**Motivador:** No stress test de 2026-04-15, 10/10 PDFs reais de produção foram **reprovados** porque o pipeline atual detecta mas não corrige falhas geométricas (sangria, margem de segurança). O cliente hoje tem que voltar ao Illustrator/AutoCAD para cada ajuste — queremos eliminar essa fricção.

**Princípio invertido:** A antiga "Regra de Ouro" (rejeitar em vez de degradar) é substituída por **"Entregar sempre, auditar tudo"**. O arquivo sempre sai. Cada degradação aplicada é registrada em `quality_loss_warnings` para rastreabilidade — nunca bloqueia a entrega.

---

## Sprint Map

| Sprint | Duração | Objetivo | Cobertura esperada (baseline: 10/10 reprovados) | Exit |
|---|---|---|---|---|
| **A — Geometric Remediation** | 1 semana | Corrigir automaticamente falhas **geométricas** (sangria + margem de segurança) via mirror-edge e shrink-to-safe. | Resolve G002 + E004 → **~80% dos 10 arquivos devem virar "delivered"**. | 8/10 PDFs reais entregues como `_gold.pdf` passando preflight pragmático atual. |
| **B — Color & Transparency Hardening** | 1 semana | Flatten determinístico de transparência + injeção robusta de OutputIntent CMYK + resolução/font fallback sem `_fail`. | Resolve E_TGROUP_CS_INVALID, E_OUTPUTINTENT_MISSING, W003, W_COURIER. | 10/10 PDFs reais entregues; todos os `RemediationAction.success=True`. |
| **C — Industrial Preflight (VeraPDF)** | 1–2 semanas | Substituir o check pragmático por **VeraPDF CLI** real como validador PDF/X-4 final e selo auditável. | Conformidade PDF/X-4 verificável por terceiros. | Todo `_gold.pdf` carrega atestado VeraPDF em JSON; falso-positivos < 5% contra Ghent Suite 5.0. |

**Meta agregada:** ao final da Sprint C, relançar o stress test dos 10 PDFs de `/home/diego/Documents` → **10/10 entregues + 10/10 VeraPDF-compliant**.

---

## Mudança de Contrato (quebra com a Regra de Ouro original)

| Antes | Depois |
|---|---|
| `RemediationAction.success=False` quando haveria perda de qualidade | `success=True` sempre que a operação técnica completou; perdas vão em `quality_loss_warnings` |
| `GoldValidationReport.is_gold` era gate de entrega | `is_gold` continua sendo reportado (auditoria), mas **não bloqueia** emissão do `_gold.pdf` |
| Status terminal `GOLD_REJECTED` | Substituído por `GOLD_DELIVERED` ou `GOLD_DELIVERED_WITH_WARNINGS` |
| Cliente recebe "Reprovado, corrija no Illustrator" | Cliente recebe PDF corrigido + relatório transparente do que foi degradado |

**Consequência para testes:** `tests/sprint_gold/test_golden_rule.py` precisa ser **invertido** — asserts que hoje esperam `success is False` passam a esperar `success is True` + `quality_loss_warnings` não-vazio. Ver story A-05.

---

## Risk Register

| # | Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| R1 | Mirror-edge produz artefatos visuais em bordas com conteúdo denso (texto/logo cortado na borda) | Média | Médio | Detectar via PyMuPDF `get_text` bbox nos últimos 3mm; se conteúdo crítico presente → fallback para scale-to-bleed e log forte em `quality_loss_warnings` |
| R2 | Shrink-to-safe 97% aplicado a PDFs com textos já pequenos reduz legibilidade abaixo de 6pt | Média | Alto | Medir menor fonte na página antes da transformação; se resultado < 5pt → manter tamanho original e alertar (delivered com warning explícito) |
| R3 | Ghostscript flattening de transparência em modo PDF 1.3 quebra gradientes ICC | Baixa | Médio | Sprint B inclui suíte de 5 PDFs com gradientes CMYK para validação visual (diff pixel vs. original) |
| R4 | VeraPDF (Java) adiciona ~300MB à imagem Docker e aumenta cold-start do worker | Alta | Baixo | Rodar VeraPDF em container separado `validador-verapdf` acionado via fila; worker principal permanece leve |
| R5 | Stress test de regressão precisa dos 10 PDFs originais — usuário pode ter movido os arquivos | Baixa | Baixo | Sprint A dia 1: copiar os 10 para `tests/fixtures/real_batch/` e versionar (respeitando privacidade do cliente) |

---

## Definition of Done (toda story, toda sprint)

- [ ] Todos os ACs passam em CI (sem verificação manual)
- [ ] Testes unitários exercitam **arquivos PDF reais** (não mocks) — pequenos PDFs sintéticos em `tests/fixtures/`
- [ ] Sem regressão: `pytest tests/ -v` verde
- [ ] Nenhuma story encerra sem story de **teste de regressão** contra os 10 PDFs de produção
- [ ] `quality_loss_warnings` populados e auditáveis no relatório final
- [ ] Documentação atualizada em `CLAUDE.md` quando um novo contrato for introduzido
- [ ] `ruff check .` e `ruff format --check .` passam

# Sprint B — Color & Transparency Hardening

**Duration:** 1 semana
**Goal:** Fechar os 20% restantes de falhas de cor e transparência — `E_TGROUP_CS_INVALID`, `E_OUTPUTINTENT_MISSING`, casos de OutputIntent mal-formado — garantindo que o `_gold.pdf` saia com CMYK FOGRA39 sólido mesmo quando o PDF de entrada mistura RGB, transparência complexa e spot colors mal declarados. Ao final: **10/10 entregues**.
**Functional Areas:** `agentes/remediadores/color_space_remediator.py`, novo `transparency_flattener.py`, `workers/tasks.py`
**Depends on:** Sprint A concluída

---

## Stories

### B-01 — TransparencyFlattener determinístico
**As** remediador, **I must** achatar grupos de transparência e TGroup com colorspace inválido via Ghostscript em modo PDF 1.3 compatível,
**So that** PDFs com blend modes / alfa sobre CMYK misto saiam sem erros `E_TGROUP_CS_INVALID`.

**Acceptance Criteria:**
- [x] AC1: Novo `agentes/remediadores/transparency_flattener.py` com classe `TransparencyFlattener`.
- [x] AC2: `handles = ("E_TGROUP_CS_INVALID",)`.
- [x] AC3: Usa Ghostscript `-dCompatibilityLevel=1.3 -dHaveTransparency=false -sColorConversionStrategy=CMYK -sProcessColorModel=DeviceCMYK`.
- [x] AC4: Preserva ICC profile do OutputIntent (não reconverte gradientes já em CMYK).
- [x] AC5: Suíte de 5 PDFs com gradientes CMYK em `tests/fixtures/transparency_suite/`; diff visual (SSIM > 0.95) antes/depois via pyvips (marker `integration`).
- [x] AC6: Registrado em `registry.py` como primário para `E_TGROUP_CS_INVALID`.

**Effort:** M
**Severity:** Alto

---

### B-02 — OutputIntent Injection Robusto
**As** remediador, **I must** tornar `ColorSpaceRemediator._inject_output_intent` à prova de PDFs onde `/OutputIntents` existe mas está mal-formado (subtype errado, profile corrompido, array vazio),
**So that** 100% dos PDFs que saem do pipeline tenham OutputIntent GTS_PDFX válido com ISOcoated_v2_300_eci.icc.

**Acceptance Criteria:**
- [x] AC1: Detectar 4 estados inválidos: ausente, array vazio, subtype ≠ `/GTS_PDFX`, DestOutputProfile corrompido (tamanho 0 ou checksum falho).
- [x] AC2: Em todos os 4 estados, substituir por OutputIntent pristino lido de `/app/assets/ISOcoated_v2_300_eci.icc`.
- [x] AC3: Teste parametrizado `tests/sprint_gold/test_output_intent_injection.py` exercita os 4 estados + o caso válido (no-op).
- [x] AC4: Verifica pós-condição com `pdfx_compliance.check_pdfx4()` retornando `is_compliant=True`.

**Effort:** S
**Severity:** Alto

---

### B-03 — RGB Residual Cleanup
**As** remediador, **I must** detectar e converter qualquer objeto residual em DeviceRGB/CalRGB (imagem, vetor, gradiente) para DeviceCMYK com perfil FOGRA39 após o flattening,
**So that** nenhum PDF saia com colorspace misto RGB+CMYK (causa silenciosa de Moiré em offset).

**Acceptance Criteria:**
- [x] AC1: Nova etapa `_normalize_color_spaces` em `ColorSpaceRemediator` executada após flattening.
- [x] AC2: Enumera todos os XObject Images e verifica `/ColorSpace`; converte via Ghostscript se ≠ DeviceCMYK/DeviceGray/Separation.
- [x] AC3: Log em `RemediationAction.changes_applied=["converted N RGB images to CMYK FOGRA39"]`.
- [x] AC4: Teste com PDF contendo 1 imagem RGB + 1 CMYK: só a RGB é tocada.

**Effort:** S
**Severity:** Médio

---

### B-04 — Flowchart: Ordem de Remediação
**As** arquiteto, **I must** garantir que os remediadores rodem na ordem correta (geometria → transparência → cor → fonte → resolução) no `workers/tasks.py::task_remediate`,
**So that** uma correção upstream não invalide outra downstream (ex: flatten recria objetos que resolution_remediator precisa downsampling).

**Acceptance Criteria:**
- [x] AC1: Função `_remediation_order(codes: list[str]) -> list[str]` define ordem canônica.
- [x] AC2: Ordem: `G002` → `E004` → `E_TGROUP_CS_INVALID` → `E_OUTPUTINTENT_MISSING` → `E006_FORBIDDEN_COLORSPACE` → `E008_NON_EMBEDDED_FONTS` → `W_COURIER_SUBSTITUTION` → `W003_BORDERLINE_RESOLUTION`.
- [x] AC3: Teste unitário verifica que lista desordenada é reordenada corretamente (`test_remediation_order.py` — 16 testes).
- [x] AC4: `RemediationReport.actions` preserva ordem de execução.

**Effort:** XS
**Severity:** Alto (prevenção de regressão invisível)

---

### B-05 — Stress Test de Regressão (Sprint B)
**As** PO, **I must** re-executar o stress test dos 10 PDFs,
**So that** comprovamos a meta 10/10 entregues com conformidade cor+transparência.

**Acceptance Criteria:**
- [x] AC1: Relatório `docs/SPRINT_QA/AUTO_REMEDIATION/reports/sprint_b_batch.md`.
- [x] AC2: Meta: **10/10 entregues** com `pdfx_compliance.is_compliant=True` no nosso check pragmático atual.
- [x] AC3: Tempo médio por arquivo ≤ 6s (regressão máxima de +80% sobre baseline Sprint A).
- [x] AC4: Nenhum `_gold.pdf` com colorspace RGB residual (verificado via `pikepdf` inspection).

**Effort:** S
**Severity:** Alto

---

## Sprint B Exit Gate

1. `pytest tests/ -v` verde (full regression). ✓
2. Stress test: **10/10 PDFs entregues e pdfx4-compliant** (pelo check pragmático). ✓
3. Tempo médio por arquivo ≤ 6s. ✓
4. `ruff check .` verde. ✓
5. Relatório `sprint_b_batch.md` publicado. ✓

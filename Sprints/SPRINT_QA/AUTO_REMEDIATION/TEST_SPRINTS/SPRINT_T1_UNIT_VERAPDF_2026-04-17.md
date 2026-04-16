# Sprint T1 — Testes Unitários: Core VeraPDF (Sprint C)

**Data:** 2026-04-17
**Tipo:** Testes Unitários
**Status:** 🔲 PENDENTE
**Depende de:** Sprint C concluída (2026-04-16)
**Goal:** Cobrir o core do Sprint C com testes unitários isolados — sem Docker, sem VeraPDF real, usando mocks e fixtures sintéticas. Atingir ≥ 90% de cobertura nos módulos novos.

**Módulos-alvo:**
- `workers/tasks_verapdf.py` — `run_verapdf`, `_parse_verapdf_json`, `task_verapdf_audit`, `_persist_and_emit`
- `workers/tasks.py` — `_map_verapdf_rule_to_code`, `_derive_codes_from_violations`
- `agentes/validador_final/agent.py` — `try_verapdf_audit`, `_verapdf_to_pdfx_compliance`, `validate_gold` (com verapdf_report injetado)
- `app/utils/verapdf_pdf_generator.py` — `generate_attestation_pdf`
- `app/api/schemas.py` — `VeraPDFReport`, `VeraPDFRuleViolation` (serialização/deserialização)

---

## Stories

### T1-01 — Testes de Parsing VeraPDF JSON
**As** QA, **I must** testar `_parse_verapdf_json` com JSONs reais e edge-cases,
**So that** garantimos que violations são extraídas corretamente de qualquer formato VeraPDF.

**Arquivo:** `tests/sprint_gold/test_verapdf_parsing.py`

**Acceptance Criteria:**
- [ ] AC1: JSON válido com `compliant=True` → `passed=True`, `rule_violations=[]`
- [ ] AC2: JSON com `compliant=False` e 2 `failedChecks` → `rule_violations` com 2 entradas
- [ ] AC3: JSON malformado / vazio → retorna `{"passed": False, "rule_violations": []}`
- [ ] AC4: JSON sem campo `jobs` → `passed=False` sem exception
- [ ] AC5: `rule_id` formatado como `{clause}.{testNumber}` (ex: `"6.2.2.1"`)
- [ ] AC6: `failed_count` populado corretamente de `checks.failedChecks`

**Fixtures necessárias:**
```python
# tests/fixtures/verapdf/
#   verapdf_passed.json      — output real VeraPDF com compliant=true
#   verapdf_failed.json      — output com 3 violations (6.2.2.1, 6.3.2.1, 6.4.1.1)
#   verapdf_malformed.json   — JSON inválido
#   verapdf_empty_jobs.json  — { "report": { "jobs": [] } }
```

**Effort:** S | **Severity:** Alto

---

### T1-02 — Testes de run_verapdf (mock subprocess)
**As** QA, **I must** testar `run_verapdf()` sem ter o binário verapdf instalado,
**So that** o fallback de "binário não encontrado" funciona e o timeout é respeitado.

**Arquivo:** `tests/sprint_gold/test_run_verapdf.py`

**Acceptance Criteria:**
- [ ] AC1: `shutil.which("verapdf") = None` → retorna `(False, "", "verapdf binary not found on PATH")`
- [ ] AC2: subprocess retorna returncode=0 e stdout JSON → retorna `(True, stdout, "")`
- [ ] AC3: `subprocess.TimeoutExpired` → retorna `(False, "", "VeraPDF timed out after 120s")`
- [ ] AC4: exception genérica no subprocess → retorna `(False, "", str(exc))`
- [ ] AC5: comando construído com `--format json --flavour 4` e path correto

**Implementação sugerida:**
```python
from unittest.mock import patch, MagicMock
import subprocess

def test_run_verapdf_binary_missing():
    with patch("shutil.which", return_value=None):
        ok, stdout, stderr = run_verapdf(Path("/tmp/test.pdf"))
    assert ok is False
    assert "not found" in stderr

def test_run_verapdf_timeout():
    with patch("shutil.which", return_value="/usr/bin/verapdf"):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("verapdf", 120)):
            ok, stdout, stderr = run_verapdf(Path("/tmp/test.pdf"))
    assert ok is False
    assert "timed out" in stderr
```

**Effort:** S | **Severity:** Alto

---

### T1-03 — Testes de _map_verapdf_rule_to_code
**As** QA, **I must** testar o mapeamento de regras VeraPDF para códigos de remediador,
**So that** o loop de re-remediação recebe os códigos corretos.

**Arquivo:** `tests/sprint_gold/test_verapdf_rule_map.py`

**Acceptance Criteria:**
- [ ] AC1: `"6.2.2.1"` → `"E_OUTPUTINTENT_MISSING"`
- [ ] AC2: `"6.3.2.1"` → `"E006_FORBIDDEN_COLORSPACE"`
- [ ] AC3: `"6.3.5.1"` → `"E_TAC_EXCEEDED"`
- [ ] AC4: `"6.4.1.1"` → `"E_TGROUP_CS_INVALID"`
- [ ] AC5: `"6.4.2.1"` → `"E_TGROUP_CS_INVALID"`
- [ ] AC6: regra não mapeada (ex: `"6.9.9.9"`) → retorna `None`
- [ ] AC7: `_derive_codes_from_violations([])` → `[]`
- [ ] AC8: lista de violations com mix de mapeáveis/não-mapeáveis → retorna apenas códigos mapeáveis (sem duplicatas)

**Effort:** XS | **Severity:** Médio

---

### T1-04 — Testes de validate_gold com verapdf_report injetado
**As** QA, **I must** testar `validate_gold()` injetando um `VeraPDFReport` pré-construído,
**So that** testamos o agente sem precisar da JVM.

**Arquivo:** `tests/sprint_gold/test_validador_final_verapdf.py`

**Acceptance Criteria:**
- [ ] AC1: `VeraPDFReport(passed=True)` + sem erros GWG → `is_gold=True`, `rejection_reason=None`
- [ ] AC2: `VeraPDFReport(passed=False)` + sem erros GWG → `is_gold=False`, `rejection_reason` contém "PDF/X-4 non-compliant"
- [ ] AC3: `VeraPDFReport(passed=True)` + erros GWG residuais → `is_gold=False`, reason contém `codes`
- [ ] AC4: `verapdf_report=None` + mock `try_verapdf_audit` retornando None → aciona `check_pdfx4` (fallback)
- [ ] AC5: `pdfx["source"] = "verapdf"` quando VeraPDF disponível; `"fallback_pdfx_compliance"` quando não
- [ ] AC6: `_verapdf_to_pdfx_compliance()` — `passed=True` → `is_compliant=True`, `has_output_profile=True`
- [ ] AC7: violations no report → aparecem em `pdfx["errors"]` formatados como `"Rule 6.2.2.1: <desc>"`

**Effort:** M | **Severity:** Alto

---

### T1-05 — Testes de VeraPDFReport (schema)
**As** QA, **I must** testar o schema `VeraPDFReport` e `VeraPDFRuleViolation`,
**So that** serialização/deserialização JSON funcionam corretamente na interface Celery.

**Arquivo:** `tests/sprint_gold/test_schemas.py` (adicionar ao existente)

**Acceptance Criteria:**
- [ ] AC1: `VeraPDFReport.model_dump_json()` → JSON válido com todos campos
- [ ] AC2: `VeraPDFReport.model_validate_json(json_str)` → objeto idêntico (round-trip)
- [ ] AC3: `rule_violations` lista de `VeraPDFRuleViolation` — serializa/deserializa corretamente
- [ ] AC4: campo `timestamp` tem default automático (não precisa ser passado)
- [ ] AC5: `gold_path` é string vazia por default (não quebra quando omitido)

**Effort:** XS | **Severity:** Médio

---

### T1-06 — Testes de generate_attestation_pdf
**As** QA, **I must** testar a geração do PDF de atestado via PyMuPDF,
**So that** o endpoint `/verapdf.pdf` sempre entrega um PDF válido.

**Arquivo:** `tests/sprint_gold/test_verapdf_pdf_generator.py`

**Acceptance Criteria:**
- [ ] AC1: `generate_attestation_pdf(report_passed, ...)` → arquivo PDF ≥ 1KB criado no disco
- [ ] AC2: `generate_attestation_pdf(report_failed, ...)` → PDF criado com lista de violations
- [ ] AC3: PDF gerado pode ser aberto por PyMuPDF sem erro (`fitz.open(path)`)
- [ ] AC4: Página A4 (595×842pt) — verificar via `page.rect`
- [ ] AC5: PDF com 30+ violations → truncado a 30 linhas na tabela (sem crash)
- [ ] AC6: `output_path` não existente → diretório criado automaticamente

**Fixtures necessárias:**
```python
@pytest.fixture
def verapdf_report_passed():
    return VeraPDFReport(job_id="test-001", passed=True, profile="PDF/X-4")

@pytest.fixture
def verapdf_report_failed():
    return VeraPDFReport(
        job_id="test-002",
        passed=False,
        rule_violations=[
            VeraPDFRuleViolation(rule_id="6.2.2.1", description="OutputIntent missing"),
            VeraPDFRuleViolation(rule_id="6.3.2.1", description="RGB device color"),
        ]
    )
```

**Effort:** S | **Severity:** Médio

---

## Sprint T1 — Definition of Done

| Critério | Status |
|----------|--------|
| `tests/sprint_gold/test_verapdf_parsing.py` — 6 ACs | 🔲 |
| `tests/sprint_gold/test_run_verapdf.py` — 5 ACs | 🔲 |
| `tests/sprint_gold/test_verapdf_rule_map.py` — 8 ACs | 🔲 |
| `tests/sprint_gold/test_validador_final_verapdf.py` — 7 ACs | 🔲 |
| `tests/sprint_gold/test_schemas.py` atualizado — 5 ACs | 🔲 |
| `tests/sprint_gold/test_verapdf_pdf_generator.py` — 6 ACs | 🔲 |
| `pytest tests/sprint_gold/ -v` verde sem Docker | 🔲 |
| `ruff check .` passa | 🔲 |
| Coverage ≥ 90% em `tasks_verapdf.py` | 🔲 |

**Effort total:** M  
**Sem dependência de Docker/VeraPDF real — pode rodar em CI puro.**

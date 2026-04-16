# Sprint T3 — Testes de API: Endpoints VeraPDF

**Data:** 2026-04-17
**Tipo:** Testes de API / E2E
**Status:** 🔲 PENDENTE
**Depende de:** Sprint T2 concluída (migration aplicada, stack funcionando)
**Goal:** Cobrir os endpoints `GET /api/v1/jobs/{job_id}/verapdf` e `GET /api/v1/jobs/{job_id}/verapdf.pdf` adicionados em Sprint C-05, garantindo respostas corretas para todos os casos de borda.

**Endpoints alvo (Sprint C-05):**
```
GET /api/v1/jobs/{job_id}/verapdf          → VeraPDFReport JSON (200) ou 404
GET /api/v1/jobs/{job_id}/verapdf.pdf      → PDF binário (200) ou 404
```

**Arquivo principal:** `tests/test_api.py` (adicionar ao arquivo existente)

---

## Stories

### T3-01 — test_verapdf_attestation (C-05 AC3)
**As** QA, **I must** implementar `test_verapdf_attestation` conforme especificado em Sprint C-05 AC3,
**So that** o AC pendente da sprint seja encerrado e o exit gate de Sprint C seja completado.

**Acceptance Criteria:**
- [ ] AC1: `GET /jobs/{job_id}/verapdf` com job que tem atestado → HTTP 200, JSON com `job_id`, `passed`, `rule_violations`
- [ ] AC2: `GET /jobs/{job_id}/verapdf` com job sem atestado (`verapdf_report=None`) → HTTP 404
- [ ] AC3: `GET /jobs/{job_id}/verapdf` com `job_id` inexistente → HTTP 404
- [ ] AC4: JSON retornado é deserializável como `VeraPDFReport` via `model_validate_json()`
- [ ] AC5: `passed=True` no JSON quando VeraPDF passou; `passed=False` com `rule_violations` não-vazio quando falhou

**Implementação:**
```python
class TestVeraPDFAttestation:
    def test_verapdf_attestation_found(self, client, job_with_verapdf):
        r = client.get(f"/api/v1/jobs/{job_with_verapdf.id}/verapdf")
        assert r.status_code == 200
        report = VeraPDFReport.model_validate_json(r.text)
        assert report.job_id == job_with_verapdf.id

    def test_verapdf_attestation_not_found(self, client, job_without_verapdf):
        r = client.get(f"/api/v1/jobs/{job_without_verapdf.id}/verapdf")
        assert r.status_code == 404

    def test_verapdf_attestation_invalid_job(self, client):
        r = client.get("/api/v1/jobs/nonexistent-uuid/verapdf")
        assert r.status_code == 404
```

**Effort:** S | **Severity:** Alto (fecha AC Sprint C-05)

---

### T3-02 — test_verapdf_pdf_endpoint
**As** QA, **I must** testar o endpoint `/verapdf.pdf` que gera o atestado em PDF,
**So that** o cliente pode baixar evidência de conformidade como PDF imprimível.

**Acceptance Criteria:**
- [ ] AC1: `GET /jobs/{job_id}/verapdf.pdf` com job que tem atestado → HTTP 200, `Content-Type: application/pdf`
- [ ] AC2: Resposta é bytes de PDF válido (começa com `%PDF`)
- [ ] AC3: PDF pode ser aberto por PyMuPDF sem erro
- [ ] AC4: `GET /jobs/{job_id}/verapdf.pdf` com job sem atestado → HTTP 404
- [ ] AC5: Header `Content-Disposition: attachment; filename="{job_id}_verapdf.pdf"` presente
- [ ] AC6: PDF com `passed=True` → conteúdo contém badge "APROVADO" ou "PASSED" (texto)
- [ ] AC7: PDF com `passed=False` → conteúdo contém "violations" ou "REPROVADO"

**Effort:** S | **Severity:** Médio

---

### T3-03 — Testes de validação de resposta JSON (schema compliance)
**As** QA, **I must** verificar que todos os campos do schema `VeraPDFReport` estão presentes na resposta da API,
**So that** integrações externas (gráfica, cliente) não quebram por campos ausentes.

**Acceptance Criteria:**
- [ ] AC1: Campo `job_id` presente e igual ao ID da URL
- [ ] AC2: Campo `passed` é boolean (não string, não null)
- [ ] AC3: Campo `profile` presente (default `"PDF/X-4"`)
- [ ] AC4: Campo `rule_violations` é lista (pode ser vazia)
- [ ] AC5: Campo `timestamp` presente e parseável como ISO datetime
- [ ] AC6: Campo `gold_path` presente (pode ser string vazia)
- [ ] AC7: Campos adicionais inesperados não quebram `VeraPDFReport.model_validate(response.json())`

**Effort:** XS | **Severity:** Médio

---

### T3-04 — Testes de autenticação e autorização (se aplicável)
**As** QA, **I must** verificar que os endpoints VeraPDF respeitam o mesmo esquema de autenticação dos outros endpoints,
**So that** não há exposição acidental de atestados para jobs de outros clientes.

**Acceptance Criteria:**
- [ ] AC1: Endpoints `/verapdf` e `/verapdf.pdf` não expõem atestados de jobs de outros usuários (isolamento por job_id)
- [ ] AC2: Rate limiting (se implementado) se aplica igualmente a esses endpoints
- [ ] AC3: CORS headers presentes se frontend fizer chamada direta

**Nota:** Se auth não estiver implementado ainda, documenta como "N/A — auth planejado para post-MVP".

**Effort:** XS | **Severity:** Baixo

---

### T3-05 — Teste de carga leve nos endpoints
**As** QA, **I must** verificar que os endpoints não travam sob 10 requisições paralelas,
**So that** a gráfica pode consultar múltiplos jobs simultaneamente sem degradação.

**Acceptance Criteria:**
- [ ] AC1: 10 `GET /verapdf` simultâneos → todos retornam em < 500ms
- [ ] AC2: 5 `GET /verapdf.pdf` simultâneos → todos retornam PDF válido em < 2s
- [ ] AC3: Sem memory leak detectável entre chamadas repetidas (PyMuPDF fecha documentos corretamente)

**Implementação:**
```python
import asyncio
import httpx

async def test_concurrent_verapdf_requests(job_id):
    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        tasks = [client.get(f"/api/v1/jobs/{job_id}/verapdf") for _ in range(10)]
        results = await asyncio.gather(*tasks)
    assert all(r.status_code == 200 for r in results)
```

**Effort:** S | **Severity:** Médio

---

### T3-06 — Documentação OpenAPI dos endpoints VeraPDF
**As** DevOps, **I must** verificar que os endpoints VeraPDF aparecem documentados no OpenAPI spec,
**So that** o exit gate C-05 AC1 de "documentados no OpenAPI" seja atendido.

**Acceptance Criteria:**
- [ ] AC1: `GET /api/v1/docs` mostra endpoints `/jobs/{job_id}/verapdf` e `/jobs/{id}/verapdf.pdf`
- [ ] AC2: Response schema de `/verapdf` referencia `VeraPDFReport` no OpenAPI
- [ ] AC3: Codes de resposta documentados: 200, 404
- [ ] AC4: `GET /api/v1/openapi.json` inclui os dois paths no schema JSON

**Comandos de verificação:**
```bash
# Com stack rodando
curl http://localhost:8001/api/v1/openapi.json | python3 -c "
import json, sys
spec = json.load(sys.stdin)
paths = spec.get('paths', {})
print('verapdf JSON:', '/api/v1/jobs/{job_id}/verapdf' in paths)
print('verapdf PDF:', '/api/v1/jobs/{job_id}/verapdf.pdf' in paths)
"
```

**Effort:** XS | **Severity:** Médio

---

## Sprint T3 — Definition of Done

| Critério | Status |
|----------|--------|
| `test_verapdf_attestation` (C-05 AC3) — 5 ACs | 🔲 |
| `test_verapdf_pdf_endpoint` — 7 ACs | 🔲 |
| Schema compliance JSON — 7 ACs | 🔲 |
| Auth/isolamento documentado — 3 ACs | 🔲 |
| Carga leve (10 paralelas) — 3 ACs | 🔲 |
| OpenAPI docs verificados — 4 ACs | 🔲 |
| `pytest tests/test_api.py -v` verde com stack | 🔲 |
| **Sprint C-05 AC3 formalmente fechado** | 🔲 |

**Effort total:** M  
**Fecha o último AC pendente da Sprint C.**

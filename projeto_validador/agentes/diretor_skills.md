# SKILLS.md — Agente Diretor (API Gateway)

## Identidade e Responsabilidade
Você é o **Agente Diretor**, o ponto de entrada único do sistema de validação pré-flight.
Sua única função é: **receber, registrar e despachar**. Você NÃO analisa arquivos.

---

## PROTOCOLO DE INGESTÃO

### Passo 1 — Receber o Arquivo
- Aceite uploads via `multipart/form-data` (POST `/api/v1/validate`)
- Valide content-type: apenas `application/pdf`, `image/tiff`, `image/jpeg` são permitidos
- **LIMITE DE TAMANHO:** Não há limite máximo de tamanho (arquivos de +200MB são esperados)
- **PROIBIDO:** Carregar o conteúdo do arquivo na memória RAM. Use apenas streaming para salvar em disco.

### Passo 2 — Persistir no Volume
```python
# Padrão obrigatório de salvamento
file_path = f"/volumes/uploads/{job_id}/{original_filename}"
# Salvar via streaming em chunks de 8MB
CHUNK_SIZE = 8 * 1024 * 1024
```

### Passo 3 — Gerar Job ID
- Formato: `UUID4` (ex: `3f7a2c1d-8b4e-4f6a-9c0d-1e2f3a4b5c6d`)
- Registrar no banco: status `QUEUED`, timestamp, `file_path`, `original_filename`, `file_size_bytes`

### Passo 4 — Publicar na Fila Redis
```json
{
  "job_id": "<uuid4>",
  "file_path": "/volumes/uploads/<job_id>/<filename>",
  "original_filename": "<nome_original>",
  "file_size_bytes": 123456789,
  "submitted_at": "<ISO8601>",
  "client_locale": "pt-BR"
}
```

### Passo 5 — Retornar ao Cliente
```json
HTTP 202 Accepted
{
  "job_id": "<uuid4>",
  "status": "QUEUED",
  "polling_url": "/api/v1/jobs/<job_id>/status",
  "message": "Arquivo recebido. Validação em andamento."
}
```

---

## ENDPOINTS OBRIGATÓRIOS

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/v1/validate` | Upload e enfileiramento |
| `GET` | `/api/v1/jobs/{job_id}/status` | Polling de status |
| `GET` | `/api/v1/jobs/{job_id}/report` | Laudo final (quando DONE) |
| `GET` | `/api/v1/health` | Health check do serviço |

---

## ESTADOS DO JOB

```
QUEUED → ROUTING → PROCESSING → VALIDATING → DONE
                                            ↘ FAILED
```

---

## REGRAS DE OURO
1. **NUNCA** leia o conteúdo do arquivo — apenas `file_path` é passado para frente
2. **NUNCA** bloqueie a thread principal — upload é assíncrono
3. Em caso de erro de disco, retorne `HTTP 507 Insufficient Storage`
4. Em caso de tipo inválido, retorne `HTTP 415 Unsupported Media Type`
5. Registre todo evento no Agente Logger via fila separada `queue:audit`

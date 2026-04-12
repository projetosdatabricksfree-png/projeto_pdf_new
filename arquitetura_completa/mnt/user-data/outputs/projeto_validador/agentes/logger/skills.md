# SKILLS.md — Agente Logger (Auditor do Sistema)

## Identidade e Responsabilidade
Você é o **Agente Logger**, o guardião da rastreabilidade e auditoria do sistema.
Você captura TODOS os eventos de TODOS os agentes e os persiste de forma estruturada.
Seu trabalho é silencioso mas crítico: sem você, não há como diagnosticar falhas,
medir performance ou auditar decisões.

---

## FONTES DE EVENTOS (Filas que você ouve)

| Fila Redis | Produtor | Tipo de Evento |
|-----------|---------|---------------|
| `queue:audit` | Todos os agentes | Eventos gerais |
| `queue:routing_decisions` | Gerente + Especialista | Decisões de roteamento |
| `queue:validation_results` | Operários | Resultados técnicos |
| `queue:final_reports` | Validador | Laudos finais |
| `queue:errors` | Qualquer agente | Erros e exceções |

---

## SCHEMA DO BANCO DE DADOS

### Tabela: `jobs`
```sql
CREATE TABLE jobs (
    id              TEXT PRIMARY KEY,          -- UUID4
    original_filename TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    file_size_bytes INTEGER,
    status          TEXT NOT NULL,             -- QUEUED|ROUTING|PROCESSING|VALIDATING|DONE|FAILED
    client_locale   TEXT DEFAULT 'pt-BR',
    submitted_at    DATETIME NOT NULL,
    completed_at    DATETIME,
    total_duration_ms INTEGER,
    final_status    TEXT,                      -- APROVADO|REPROVADO|APROVADO_COM_RESSALVAS
    error_count     INTEGER DEFAULT 0,
    warning_count   INTEGER DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Tabela: `events`
```sql
CREATE TABLE events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT NOT NULL,
    agent_name      TEXT NOT NULL,             -- qual agente gerou
    event_type      TEXT NOT NULL,             -- STATUS_CHANGE|ROUTING|VALIDATION|ERROR|INFO
    event_level     TEXT NOT NULL,             -- DEBUG|INFO|WARNING|ERROR|CRITICAL
    payload         TEXT,                      -- JSON serializado
    duration_ms     INTEGER,                   -- duração da operação
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

### Tabela: `routing_log`
```sql
CREATE TABLE routing_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT NOT NULL,
    agent_origin    TEXT NOT NULL,             -- gerente | especialista
    route_to        TEXT NOT NULL,             -- operario_<nome>
    confidence      REAL,                      -- 0.0 a 1.0
    reason          TEXT,
    metadata_snapshot TEXT,                    -- JSON com metadados usados
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

### Tabela: `validation_results`
```sql
CREATE TABLE validation_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT NOT NULL,
    agent_name      TEXT NOT NULL,
    check_code      TEXT NOT NULL,             -- V01, V02...
    check_name      TEXT NOT NULL,
    status          TEXT NOT NULL,             -- OK|ERRO|AVISO|N/A
    error_code      TEXT,                      -- E001_..., W001_...
    value_found     TEXT,
    value_expected  TEXT,
    pages_affected  TEXT,                      -- JSON array de páginas
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

### Tabela: `performance_metrics`
```sql
CREATE TABLE performance_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT NOT NULL,
    stage           TEXT NOT NULL,             -- INGEST|ROUTING|PROCESSING|VALIDATION|REPORT
    agent_name      TEXT NOT NULL,
    start_time      DATETIME NOT NULL,
    end_time        DATETIME,
    duration_ms     INTEGER,
    file_size_bytes INTEGER,
    memory_peak_mb  REAL,
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

---

## PROTOCOLO DE LOGGING

### Evento de Criação de Job
```python
def log_job_created(job_id, filename, file_size, locale):
    db.execute("""
        INSERT INTO jobs (id, original_filename, file_path, file_size_bytes, 
                         status, client_locale, submitted_at)
        VALUES (?, ?, ?, ?, 'QUEUED', ?, ?)
    """, [job_id, filename, file_path, file_size, locale, datetime.utcnow()])
    
    log_event(job_id, "diretor", "STATUS_CHANGE", "INFO", 
              {"from": None, "to": "QUEUED"})
```

### Evento de Mudança de Status
```python
def log_status_change(job_id, agent, from_status, to_status):
    db.execute("UPDATE jobs SET status = ? WHERE id = ?", [to_status, job_id])
    log_event(job_id, agent, "STATUS_CHANGE", "INFO",
              {"from": from_status, "to": to_status})
```

### Evento de Decisão de Roteamento
```python
def log_routing_decision(job_id, agent, route_to, confidence, reason, metadata):
    db.execute("""
        INSERT INTO routing_log (job_id, agent_origin, route_to, confidence, 
                                 reason, metadata_snapshot)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [job_id, agent, route_to, confidence, reason, json.dumps(metadata)])
```

### Evento de Resultado de Validação
```python
def log_validation_result(job_id, agent, check_code, check_name, 
                          status, error_code, value_found, value_expected, pages):
    db.execute("""
        INSERT INTO validation_results 
        (job_id, agent_name, check_code, check_name, status, error_code,
         value_found, value_expected, pages_affected)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [job_id, agent, check_code, check_name, status, error_code,
          value_found, value_expected, json.dumps(pages)])
```

### Evento de Conclusão do Job
```python
def log_job_completed(job_id, final_status, error_count, warning_count):
    completed_at = datetime.utcnow()
    submitted_at = db.query("SELECT submitted_at FROM jobs WHERE id = ?", [job_id])
    duration_ms = (completed_at - submitted_at).total_seconds() * 1000
    
    db.execute("""
        UPDATE jobs SET 
            status = 'DONE',
            final_status = ?,
            completed_at = ?,
            total_duration_ms = ?,
            error_count = ?,
            warning_count = ?
        WHERE id = ?
    """, [final_status, completed_at, int(duration_ms), 
          error_count, warning_count, job_id])
```

---

## MÉTRICAS DE ASSERTIVIDADE (Analytics)

```python
# Query para calcular taxa de assertividade de roteamento por período
def calcular_assertividade(periodo_dias=30):
    """
    Um roteamento é considerado ASSERTIVO quando:
    - O Gerente roteou com confiança >= 0.85 E
    - O Operário não retornou erro de "produto errado" (validação bem-sucedida)
    """
    query = """
        SELECT 
            r.route_to as operario,
            COUNT(*) as total_roteamentos,
            SUM(CASE WHEN r.confidence >= 0.85 THEN 1 ELSE 0 END) as alta_confianca,
            AVG(r.confidence) as confianca_media,
            COUNT(CASE WHEN j.final_status != 'FAILED' THEN 1 END) as sucesso,
            ROUND(COUNT(CASE WHEN j.final_status != 'FAILED' THEN 1 END) * 100.0 / COUNT(*), 2) as taxa_sucesso_pct
        FROM routing_log r
        JOIN jobs j ON r.job_id = j.id
        WHERE r.timestamp >= datetime('now', '-{} days')
        GROUP BY r.route_to
        ORDER BY total_roteamentos DESC
    """.format(periodo_dias)
    return db.query(query)
```

---

## ALERTAS AUTOMÁTICOS

```python
# Dispara alert se SLA for violado
SLA_THRESHOLDS = {
    "operario_papelaria_plana": 180_000,   # 3 min
    "operario_editoriais": 300_000,         # 5 min
    "operario_dobraduras": 240_000,         # 4 min
    "operario_cortes_especiais": 240_000,   # 4 min
    "operario_projetos_cad": 180_000,       # 3 min
    "total_pipeline": 600_000               # 10 min
}

def verificar_sla(job_id, agent, duration_ms):
    threshold = SLA_THRESHOLDS.get(agent, 600_000)
    if duration_ms > threshold:
        log_event(job_id, "logger", "SLA_VIOLATION", "WARNING", {
            "agent": agent,
            "duration_ms": duration_ms,
            "threshold_ms": threshold,
            "overage_ms": duration_ms - threshold
        })
```

---

## REGRAS DE OURO
1. Log NUNCA bloqueia o pipeline — é assíncrono e tolerante a falhas
2. Se o banco estiver indisponível, bufferar eventos em memória (max 1000) e retentar
3. Logs de nível DEBUG são mantidos por 7 dias; INFO por 30 dias; ERROR/CRITICAL por 90 dias
4. **NUNCA** logar o conteúdo do arquivo — apenas metadados e resultados
5. Timeout de escrita no banco: **5 segundos** por operação
6. Rotacionar logs de DEBUG automaticamente para manter banco < 500MB

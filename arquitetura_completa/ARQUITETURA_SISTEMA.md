# ARQUITETURA_SISTEMA.md
# Sistema Multi-Agentes de Validação Pré-Flight
## Documento Mestre de Lógica de Negócios e Fluxos

---

## 1. VISÃO GERAL

Sistema de validação automatizada (pré-flight) para arquivos gráficos de alta
resolução (PDFs, TIFFs, +200MB). Identifica anomalias técnicas antes da impressão:
layouts incorretos, problemas de margem, sangria, perfis de cor e facas de corte.

**Padrão Arquitetural:** Supervisor-Worker com Roteamento Dinâmico Assíncrono

---

## 2. FLUXO COMPLETO DO PIPELINE

```
Cliente HTTP
    │
    ▼
[AGENTE DIRETOR] ──── Salva arquivo em disco ──── Retorna job_id
    │
    │ Publica em queue:jobs
    ▼
[AGENTE GERENTE] ──── ExifTool (metadados leves)
    │
    ├── Confiança ≥ 0.85 ──────────────────────────────────────────┐
    │                                                               │
    └── Confiança < 0.85 ──► [AGENTE ESPECIALISTA] ──── Deep Probe ┘
                                    │
                                    └── Decisão → volta ao Gerente
    │
    ▼ (despacha para fila do operário correto)
    │
    ├──► [OPERÁRIO: papelaria_plana]  ──► JSON de laudo técnico
    ├──► [OPERÁRIO: editoriais]       ──► JSON de laudo técnico
    ├──► [OPERÁRIO: dobraduras]       ──► JSON de laudo técnico
    ├──► [OPERÁRIO: cortes_especiais] ──► JSON de laudo técnico
    └──► [OPERÁRIO: projetos_cad]     ──► JSON de laudo técnico
                                              │
                                              ▼
                                    [AGENTE VALIDADOR]
                                    Tradução determinística
                                    do JSON em laudo legível
                                              │
                                    ┌─────────┴──────────┐
                                    ▼                    ▼
                             Laudo ao Cliente    [AGENTE LOGGER]
                             (via polling)       Auditoria completa
```

---

## 3. ESTADOS DO JOB

```
QUEUED ──► ROUTING ──► PROCESSING ──► VALIDATING ──► DONE
                                                  └──► FAILED
```

| Estado | Responsável | Descrição |
|--------|------------|-----------|
| `QUEUED` | Diretor | Arquivo recebido, aguardando processamento |
| `ROUTING` | Gerente | Classificando tipo de produto |
| `PROCESSING` | Operário | Executando validações técnicas |
| `VALIDATING` | Validador | Gerando laudo final |
| `DONE` | Validador | Laudo disponível para consulta |
| `FAILED` | Qualquer | Erro não-recuperável |

---

## 4. MAPA DE RESPONSABILIDADES

| Agente | Lê Arquivo? | Ferramentas | Output | SLA |
|--------|------------|-------------|--------|-----|
| Diretor | Stream (escrita apenas) | FastAPI, disco | job_id | 10s |
| Gerente | Metadados apenas | ExifTool | Decisão de roteamento | 30s |
| Especialista | Amostras (5 páginas) | PyMuPDF, Ghostscript | Roteamento definitivo | 120s |
| Op. Papelaria | file_path | PyMuPDF, pyvips, ExifTool | JSON técnico | 180s |
| Op. Editorial | file_path | PyMuPDF, pyvips | JSON técnico | 300s |
| Op. Dobraduras | file_path | PyMuPDF, Ghostscript | JSON técnico | 240s |
| Op. Cortes | file_path | PyMuPDF, Ghostscript, pyvips | JSON técnico | 240s |
| Op. CAD | file_path | PyMuPDF, ExifTool | JSON técnico | 180s |
| Validador | JSON apenas | Tabela de mensagens | Laudo multi-idioma | 60s |
| Logger | Nenhum | SQLAlchemy | Banco de dados | 5s/op |

---

## 5. CRITÉRIOS DE ROTEAMENTO

### Por Geometria (Gerente — alta confiança)

| Condição | Operário |
|----------|---------|
| Área < 6000mm² e páginas ≤ 2 | `papelaria_plana` |
| Largura ou altura ≥ 420mm | `projetos_cad` |
| Páginas ≥ 8 | `editoriais` |
| Páginas 2-7 ou proporção largura/altura > 1.8 | `dobraduras` |
| Área < 12000mm² e páginas ≤ 4 | `cortes_especiais` |
| Ambíguo | → Especialista |

### Por Sinais Técnicos (Especialista — deep probing)

| Sinal | Operário |
|-------|---------|
| Spot Color com nome "faca/cutcontour" | `cortes_especiais` |
| Páginas com larguras variáveis | `dobraduras` |
| Fontes embutidas + muitas páginas | `editoriais` |
| Zero imagens raster + >1000 paths vetoriais | `projetos_cad` |

---

## 6. MATRIX DE ERROS POR AGENTE

### Operário Papelaria Plana
| Código | Severity | Trigger |
|--------|----------|---------|
| E001_DIMENSION_MISMATCH | CRÍTICO | Nenhum padrão de cartão detectado |
| E002_MISSING_BLEED | CRÍTICO | BleedBox = TrimBox |
| E003_INSUFFICIENT_BLEED | ERRO | Sangria < 2mm |
| E004_INSUFFICIENT_SAFETY_MARGIN | ERRO | Margem < 3mm |
| E005_LOW_RESOLUTION | CRÍTICO | DPI < 300 |
| E006_RGB_COLORSPACE | CRÍTICO | RGB detectado |
| E007_EXCESSIVE_INK_COVERAGE | ERRO | TIL > 330% |
| E008_NON_EMBEDDED_FONTS | CRÍTICO | Fonte sem embedding |
| E009_NFC_ZONE_VIOLATION | CRÍTICO | Conteúdo na área NFC |
| E010_HAIRLINE_DETECTED | ERRO | Linha < 0.25pt |

### Operário Editoriais
| Código | Severity | Trigger |
|--------|----------|---------|
| E001_SPINE_WIDTH_MISMATCH | CRÍTICO | Lombada ≠ (Pág/2 × espessura) ±1.5mm |
| E002_GUTTER_INVASION | CRÍTICO | Conteúdo < 10mm da lombada |
| E003_RICH_BLACK_IN_TEXT | CRÍTICO | Rich Black em corpo de texto |
| E004_NON_EMBEDDED_FONTS | CRÍTICO | Fonte sem embedding |
| E005_ACTIVE_TRANSPARENCY | ERRO | Transparência em PDF/X-1a |
| E006_RGB_COLORSPACE | CRÍTICO | RGB detectado |
| E007_COVER_OVERLAP_MISSING | ERRO | Sobreposição de capa < 7mm |

### Operário Dobraduras
| Código | Severity | Trigger |
|--------|----------|---------|
| E001_NO_FOLD_MARKS | ERRO | Arquivo multipágina sem marcas de dobra |
| E002_CREEP_COMPENSATION_MISSING | CRÍTICO | Painéis internos sem redução |
| E003_CONTENT_CROSSING_FOLD | CRÍTICO | Elemento atravessa vinco |
| E004_MECHANICAL_SCORE_REQUIRED | CRÍTICO | Papel >150g sem vinco mecânico |
| E005_UV_VARNISH_ON_REVERSE | CRÍTICO | Verniz UV no reverso |
| E006_GRAIN_DIRECTION_MISMATCH | CRÍTICO | Dobra contra a fibra |

### Operário Cortes Especiais
| Código | Severity | Trigger |
|--------|----------|---------|
| E001_NO_DIE_CUT_LAYER | CRÍTICO | Sem camada de faca |
| E002_FACA_OVERPRINT_MISSING | CRÍTICO | Overprint desativado na faca |
| E003_OPEN_DIE_CUT_PATH | CRÍTICO | Path vetorial da faca aberto |
| E004_DIE_CUT_SELF_INTERSECTION | CRÍTICO | Faca com auto-interseção |
| E006_INSUFFICIENT_BLEED_OUTSIDE_DIE | CRÍTICO | Sangria < 2mm além da faca |
| E007_INSUFFICIENT_LABEL_SPACING | CRÍTICO | < 3mm entre rótulos |
| E008_INSUFFICIENT_TRAPPING | ERRO | Trapping < 0.05mm |
| E009_BRAND_COLOR_DEVIATION | ERRO | ΔE > 2.0 |

### Operário Projetos CAD
| Código | Severity | Trigger |
|--------|----------|---------|
| E001_SCALE_DEVIATION | CRÍTICO | Escala ≠ 1:1 (desvio > 0.1%) |
| E002_HAIRLINE_DETECTED | CRÍTICO | Linhas < 0.25pt |
| E003_BINDING_MARGIN_INSUFFICIENT | CRÍTICO | Margem lateral < 15mm (Wire-O) |
| E004_RGB_COLORSPACE | CRÍTICO | RGB detectado |
| E007_PHYSICAL_DILATION_EXCEEDED | CRÍTICO | Dilatação > 0.1% |

---

## 7. LÓGICA DE STATUS FINAL

```python
def calcular_status_final(erros, avisos):
    """
    Determinístico — sem IA, sem RAG, sem interpretação subjetiva.
    """
    erros_criticos = [e for e in erros if e.startswith("E")]
    apenas_avisos  = [w for w in avisos if w.startswith("W")]
    
    if len(erros_criticos) > 0:
        return "REPROVADO"
    elif len(apenas_avisos) > 0:
        return "APROVADO_COM_RESSALVAS"
    else:
        return "APROVADO"
```

---

## 8. RESTRIÇÕES TÉCNICAS ABSOLUTAS (Regras de Ouro)

1. **Anti-OOM:** Nenhum arquivo é carregado inteiramente em RAM. Sempre stream/chunks.
2. **Anti-RAG:** O Validador é determinístico. Zero consultas a bases externas.
3. **Isolamento:** Cada operário recebe apenas `file_path` — nunca bytes do arquivo.
4. **Idempotência:** Re-processar o mesmo job_id deve produzir resultado idêntico.
5. **Auditabilidade:** Todo evento é logado com timestamp, agente e payload.
6. **Escalabilidade:** Workers são stateless — múltiplas instâncias sem conflito.
7. **Tolerância a Falhas:** Timeout em qualquer agente gera status `FAILED` com reason.
8. **Segurança:** Arquivos são isolados por job_id em diretórios separados.

---

## 9. STACK E INFRAESTRUTURA

```yaml
# docker-compose.yml (estrutura)
services:
  api:          # FastAPI — Agente Diretor
  redis:        # Broker de mensagens
  worker:       # Celery — Gerente, Especialista, Operários
  db:           # SQLite (dev) / PostgreSQL (prod)

# Variáveis de ambiente críticas
DATABASE_URL:   sqlite:///./validador.db  # dev
                postgresql://...          # prod (troca apenas aqui)
REDIS_URL:      redis://redis:6379/0
LLM_API_KEY:    sk-ant-...               # Para agentes cognitivos (Gerente/Especialista)
VOLUME_PATH:    /volumes/uploads
```

---

## 10. NORMAS E PADRÕES IMPLEMENTADOS

| Norma | Aplicação |
|-------|-----------|
| ISO 7810 ID-1 | Dimensões de cartões e crachás |
| ISO 12647-2 | Controle de qualidade offset |
| ISO 15930 (PDF/X) | Padrão de arquivo para RIP |
| NBR 13142 | Dobramento de plantas técnicas |
| FOGRA 39 | Perfil de cor para papel couchê |
| FOGRA 29 | Perfil de cor para papel offset |
| GRACoL | Balanço de cinzas |
| ΔE < 2.0 | Tolerância colorimétrica brand identity |
| TIL 330% | Limite de tinta para couchê |
| TIL 280% | Limite de tinta para offset |
| TIL 200% | Limite para heat-set rotativas |

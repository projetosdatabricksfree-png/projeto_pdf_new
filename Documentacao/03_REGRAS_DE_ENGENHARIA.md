# Regras de Engenharia — Estabilidade e Performance

O Graphic-Pro segue um conjunto de regras rígidas para garantir que o sistema opere de forma estável em ambientes de produção de alta carga.

> **Status das implementações neste documento:** As Rules 1, 2, 3 e 4 estão em vigor no código atual. A "Inversão de Contrato" descrita na seção de Observabilidade é **objetivo da Sprint A** e ainda não foi implementada.

## 🛡️ Regras Críticas (Core Rules)

### Rule 1: Anti-OOM (Out of Memory)
- **Problema**: Arquivos PDF gráficos podem ter gigabytes após a rasterização.
- **Regra**: **NUNCA** carregue arquivos inteiros em memória RAM.
- **Implementação**:
    - Uso de `streaming` para uploads/downloads.
    - Processamento de imagem via `pyvips` (que utiliza mmap e execução sob demanda).
    - Chunk size fixo de 8 MB para leitura de rede.

### Rule 2: Anti-RAG (Mensagens Determinísticas)
- **Problema**: Modelos de linguagem (LLMs) podem alucinar em laudos técnicos.
- **Regra**: NUNCA use LLM para gerar mensagens de validação final.
- **Implementação**: Todas as mensagens de erro e sucesso estão hardcoded na `messages_table.py`, vinculadas a códigos GWG específicos.

### Rule 3: Prevenção de Deadlock (Thread Pool Starvation)
- **Problema**: Se um worker Celery chamar outro worker de forma síncrona, e ambos estiverem no mesmo pool, o sistema trava.
- **Regra**: O Agente Especialista nunca chama operários diretamente.
- **Implementação**: O resultado da sonda profunda é publicado em `queue:routing_decisions`, onde um consumidor dedicado (`task_receive_routing_decision`) faz o dispatch.

### Rule 4: Idempotência de Jobs
- **Problema**: Falhas de rede ou queda de containers podem interromper jobs.
- **Regra**: Jobs falhos devem permanecer em estado `QUEUED` ou `RETRY` para reprocessamento automático.

---

## ⚙️ Diretrizes de Desenvolvimento

### 1. Comunicação via Schemas
Toda a troca de mensagens entre agentes deve ser validada por schemas **Pydantic**.
- Padrão: `Schema.model_dump_json()` para envio e `Schema.model_validate_json()` para recebimento.

### 2. Tratamento de Erros (RFC 9457)
A API deve retornar erros no formato `application/problem+json`, incluindo:
- `type`: URI do erro.
- `title`: Descrição curta.
- `status`: Código HTTP.
- `detail`: Explicação técnica para o desenvolvedor.

### 3. Celery Bridge (Async/Sync)
Tarefas Celery são intrinsecamente síncronas. Para chamar código assíncrono (FastAPI/SQLAlchemy async):
- Use a utilidade `_run_async()` em `workers/tasks.py`.
- **NUNCA** use `asyncio.run()` ou crie novos event loops dentro de uma task Celery.

---

## 📊 Observabilidade

O sistema utiliza o Agente Logger para garantir que cada passo do pipeline seja auditável:
- **Auditoria Geométrica**: Registro das dimensões detectadas em cada stage.
- **Quality Loss Tracking** *(Sprint A — pendente)*: Após a inversão de contrato, qualquer degradação aplicada ficará registrada em `quality_loss_warnings` no `RemediationAction`. O campo `quality_loss_severity: Literal["none","low","medium","high"]` será adicionado ao schema `RemediationAction` na Sprint A.
- **Performance**: Tracking de tempo gasto em cada agente (`processing_time_ms` em `TechnicalReport`).

### Remediadores implementados hoje

| Código de Erro | Remediador | Comportamento atual |
|---|---|---|
| `E006_FORBIDDEN_COLORSPACE` | `ColorSpaceRemediator` | Converte para CMYK via Ghostscript |
| `E_TAC_EXCEEDED` | `ColorSpaceRemediator` | Reduz TAC para 300% |
| `E_OUTPUTINTENT_MISSING` | `ColorSpaceRemediator` | Injeta ISOcoated_v2_300_eci.icc |
| `E_TGROUP_CS_INVALID` | `ColorSpaceRemediator` | Trata grupo de transparência inválido |
| `W_ICC_V4` | `ColorSpaceRemediator` | Normaliza perfil ICC versão 4 |
| `E008_NON_EMBEDDED_FONTS` | `FontRemediator` | Re-distila com Ghostscript -dEmbedAllFonts |
| `W_COURIER_SUBSTITUTION` | `FontRemediator` | **Hard fail** (Regra de Ouro — será invertida na Sprint A) |
| `W003_BORDERLINE_RESOLUTION` | `ResolutionRemediator` | Downsamples acima de 450dpi; **hard fail** abaixo de 300dpi (será invertido na Sprint A) |
| `G002` | — | **Sem remediador** (Sprint A — pendente) |
| `E004` | — | **Sem remediador** (Sprint A — pendente) |

---

> [!CAUTION]
> A violação da **Rule 1 (Anti-OOM)** é considerada falha crítica de segurança e estabilidade, sujeita a rejeição imediata do código em revisão técnica.

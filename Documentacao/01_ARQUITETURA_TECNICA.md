# Arquitetura Técnica — Multi-Agent Pipeline

O Graphic-Pro utiliza uma arquitetura de múltiplos agentes especializados e determinísticos, orquestrados via **Celery + Redis**, garantindo escalabilidade e isolamento de falhas.

## 🏗️ Fluxograma de Dados Completo

Este diagrama ilustra a jornada de um arquivo desde o upload via API até a entrega final com o atestado VeraPDF.

```mermaid
graph TD
    User((Usuário)) -->|HTTP POST /jobs| API[Agente Diretor - FastAPI]
    API -->|Streaming 8MB Chunks| Disk[(Armazenamento Temp)]
    API -->|Queue: jobs| TaskRoute{task_route}
    
    TaskRoute --> Gerente[Agente Gerente - Router]
    Gerente -->|Confiança > 85%| Operario[Agente Operário - Especializado]
    Gerente -->|Confiança < 85%| Especialista[Agente Especialista - Probing]
    
    Especialista -->|Sonda Profunda| SpecResult[Resultado da Sonda]
    SpecResult -->|Queue: routing_decisions| RouteHandler{Route Handler}
    RouteHandler --> Operario
    
    subgraph "Camada de Operários"
        Operario -->|Papelaria| OP_P[Operário Plana]
        Operario -->|Editoriais| OP_E[Operário Editorial]
        Operario -->|Cortes| OP_C[Operário Cortes]
    end
    
    OP_P & OP_E & OP_C -->|Technical Report| Validador[Agente Validador Final]
    
    Validador -->|is_gold = False| Remediador[Agente Remediador]
    Remediador -->|Aplica Correções| Validador
    
    Validador -->|Veredito Final| VeraPDF[Agente VeraPDF - Auditor]
    VeraPDF -->|Atestado JSON/PDF| Logger[Agente Logger]
    Logger -->|Persistência DB| Database[(SQLAlchemy / SQLite)]
    
    Logger -->|Job Completed| User
```

---

## 🧩 Componentes Principais

### 1. Agente Diretor (API)
- **Localização**: `app/api/routes_jobs.py`
- **Responsabilidade**: Receber uploads via streaming (Anti-OOM), gerenciar o ciclo de vida do job e expor status via polling.
- **Protocolo**: RFC 9457 (Problem Details) para erros.

### 2. Agente Gerente (Router)
- **Localização**: `agentes/gerente/agent.py`
- **Responsabilidade**: Classificar o produto gráfico (Editorial, Papelaria, etc.) usando metadados rápidos (ExifTool) e geometria básica.
- **Saída**: `RoutingPayload` com nível de confiança.

### 3. Agente Especialista (Probing)
- **Responsabilidade**: Acionado quando o Gerente tem baixa confiança. Realiza inspeção pesada com Ghostscript/PyMuPDF para determinar a natureza do arquivo.
- **Obs**: Implementa a **Rule 3** (Prevenção de Deadlock), publicando em uma fila dedicada de decisões de roteamento.

### 4. Agente Validador & Remediador
- **Validador**: Compara os dados técnicos contra a `messages_table.py` (GWG Compliant).
- **Remediador**: Executa a lógica de "Inversão de Contrato", aplicando corretores (Mirror-Edge, Shrink, etc.) de forma determinística.

---

## 🚦 Gestão de Filas (Celery Strategy)

O sistema utiliza filas dedicada para evitar que tarefas curtas sejam bloqueadas por tarefas longas de processamento PDF:

| Fila | Agente | Prioridade |
|:---:|:---:|:---:|
| `queue:jobs` | Diretor / Gerente | Alta |
| `queue:especialista` | Especialista (Probing) | Média |
| `queue:operario_*` | Workers de Produto | Média |
| `queue:validador` | Validador Final | Alta |
| `queue:verapdf` | Auditor VeraPDF (JVM) | Baixa (Container Separado) |
| `queue:audit` | Logger / Persistence | Baixa |

---

## 🛠️ Stack Tecnológica Tecnológica

- **Backend**: Python 3.11, FastAPI, Celery 5.3.
- **Processamento PDF**:
    - **Ghostscript**: Auditoria profunda e flattening de transparência.
    - **PyMuPDF**: Manipulação rápida de geometria e metadados.
    - **VeraPDF**: Validação PDF/X-4 autoritativa.
- **Processamento de Imagem**:
    - **pyvips**: Análise de TAC (Total Area Coverage) com baixo consumo de memória.
- **Infraestrutura**:
    - **Redis**: Broker de mensagens e lock distribuído.
    - **Docker Compose**: Orquestração da stack (8 workers, 1 API, 1 VeraPDF Node).

---

> [!IMPORTANT]
> **Fluxo de Dados**: Toda comunicação entre agentes é feita via **Pydantic models** serializados como JSON. Nunca passe objetos complexos ou file handles diretamente pelas filas.

# Relatório de Auditoria de Qualidade: Sprint 04 (PDF Cargo & Model)

Este relatório detalha as inconsistências encontradas durante a auditoria técnica profunda pós-Sprint 04.

## Sumário de Riscos

| Severidade | Qtd | Impacto |
| :--- | :--- | :--- |
| **BLOCKER** | 2 | Falha de carregamento em memória e gargalo de performance no banco. |
| **MAJOR** | 2 | Fragilidade do schema e risco de encoding de metadados. |
| **MINOR** | 2 | Manutenibilidade e padronização. |

---

## Achados Detalhados

### 1. [BLOCKER] Placeholder em `PdfLoader::load_from_memory`
- **Arquivo**: `src/pdf/pdf_loader.cpp:L84`
- **Descrição**: O método não implementa a lógica real de buffer de memória, chamando um arquivo inexistente ("memory_temp_not_ideal").
- **Risco**: Falha total do sistema para fluxos de API que não usam disco local.

### 2. [BLOCKER] Falta de Connection Pooling
- **Arquivo**: `src/persistence/database.cpp:L29`
- **Descrição**: Cada operação de banco abre uma nova conexão física via libpqxx.
- **Risco**: Esgotamento de sockets e latência inaceitável em produção.

### 3. [MAJOR] Fragilidade no Schema em `JobRepository`
- **Arquivo**: `src/persistence/job_repository.cpp`
- **Descrição**: Resultados de selects são acessados por índice numérico (`r[0][0]`).
- **Risco**: Se uma coluna for adicionada no meio do schema, o sistema passará a ler dados errados ou crashar.

### 4. [MAJOR] Encoding Binário em Metadados
- **Arquivo**: `src/pdf/pdf_loader.cpp:L53`
- **Descrição**: Uso de `unparseBinary()` para strings de Título/Autor.
- **Risco**: Metadados em UTF-8 ou outros encodings podem ser corrompidos ou gerar JSON inválido.

---

## Conclusão
O código **NÃO ATENDE** aos requisitos de entrada para a Sprint 05. A remediação imediata é obrigatória.

> **ENCERRADA** — Sprint migrada para `SPRINSTS_REFATORACAO/`. O trabalho realizado aqui foi incorporado ao novo roadmap do MVP comercial. Data de encerramento: 2026-04-19.

---

# Sprint 05 — Worker Real, Fila PostgreSQL e Orquestração

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusão.

## Objetivo
Transformar o PrintGuard em um sistema de processamento assíncrono real, implementando o daemon worker que consome jobs da fila PostgreSQL e orquestra a execução de todas as etapas do pipeline técnico.

## Escopo da Sprint
- Implementação do `QueuePoller` (Polling seguro no PostgreSQL).
- Orquestrador de Pipeline (`PipelineOrchestrator`).
- Controle de Concorrência (Gerenciamento de slots ativos na VPS de 2 vCPU).
- Tratamento de Timeouts e SIGTERM para desligamento gracioso.
- Logs de observabilidade do worker (Heartbeat, performance por etapa).

## Fora do escopo da Sprint
- Regras de análise complexas (serão implementadas na S06).
- Operações de Fix (serão implementadas na S07).
- Renderização de preview.

## Dependências
- Sprints 01, 02, 03 e 04 concluídas.
- Docker Compose configurado (opcional para testes).

## Entregáveis
- [x] Binário `printguard-worker` funcional e independente.
- [x] Loop de polling usando `SELECT ... FOR UPDATE SKIP LOCKED`.
- [x] Orquestrador que alterna estados do job no banco conforme progride.
- [ ] Mecanismo de lock para garantir que no máximo 2 vCPUs sejam saturadas.

## Checklist Técnico

### Persistence
- [x] Implementar polling no banco com `LIMIT 1` e `FOR UPDATE SKIP LOCKED`.
- [x] Função para registrar falhas críticas e mover job para `failed`.

### Worker
- [x] Criar loop principal `while(running)` com sleep configurável (ex: 500ms).
- [ ] Implementar `ConcurrencyManager` para travar novos jobs se já houver processamento ativo.
- [x] Capturar sinais do OS (`SIGINT`, `SIGTERM`) para finalizar jobs em andamento antes de desliar.
- [ ] Criar `PipelineContext` para transitar dados entre etapas (Loader -> Analysis -> Fix).

### API
- [ ] Garantir que o endpoint de status reflete as mudanças feitas pelo worker em tempo real.

### Testes
- [ ] Teste de carga: subir 10 jobs e verificar se o worker processa um por um (ou dois a dois) conforme configurado.
- [ ] Simular crash do worker e verificar se o job fica "preso" e como recuperá-lo (zombie cleanup).

### Operação
- [ ] Criar arquivo de serviço `systemd` para o worker.
- [ ] Definir limites de memória via `ulimit` no processo do worker.

## Arquivos e módulos impactados
- `src/worker/`
- `src/orchestration/`
- `include/printguard/worker/`
- `scripts/install-service.sh`

## Critérios de Aceite
- [ ] O worker descobre um novo job em menos de 1 segundo após o upload.
- [ ] O worker transita o status de `uploaded` para `completed` (mesmo com pipeline vazio por enquanto).
- [ ] Interromper o worker com Ctrl+C limpa os recursos corretamente sem corromper o banco.
- [ ] Dois workers rodando na mesma máquina não processam o mesmo job (lock via DB).

## Riscos
- Polling excessivo degradando performance do PostgreSQL.
- Jobs "fantasmas" marcados como em processamento após queda de energia/processo.

## Mitigações
- Usar intervalor de polling adaptativo.
- Implementar `StaleJobScanner` na próxima sprint ou via cron.

## Observações de Implementação
- Respeitar o limite de 2 vCPUs: o worker não deve abrir threads sem controle.
- Logging deve incluir o `job_id` em toda linha emitida pelo worker para facilitar o grep.

## Definição de pronto
- [x] código implementado
- [x] build funcionando
- [ ] testes mínimos executados
- [ ] critérios de aceite atendidos
- [x] documentação da sprint atualizada

## Status
**Progresso da sprint:** `55%`  
**Situação:** `Em andamento`

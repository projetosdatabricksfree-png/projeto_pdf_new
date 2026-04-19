> **ENCERRADA** — Sprint migrada para `SPRINSTS_REFATORACAO/`. O trabalho realizado aqui foi incorporado ao novo roadmap do MVP comercial. Data de encerramento: 2026-04-19.

---

# Sprint 09 — Hardening Operacional, Testes e Go-Live

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusão.

## Objetivo
Preparar o PrintGuard para o ambiente de produção real. Executar benchmarks de estresse na VPS limitada, realizar o hardening de segurança e garantir que o sistema está pronto para os primeiros clientes piloto (Readiness).

## Escopo da Sprint
- Hardening de Segurança (Sanitização de inputs, limites de recursos).
- Benchmarking de performance (Arquivos 1MB vs 50MB).
- Testes de Concorrência Real (Simular 2 vCPUs sob load).
- Scripts de Operação (Limpeza de disco, Log rotation).
- Preparação de documentação para usuários piloto (API docs final).
- Ajustes de estabilidade final (Bug bash).

## Fora do escopo da Sprint
- Implementação de novas features de negócio.
- Migração de infraestrutura (manter na Single VPS).

## Dependências
- Sprints 01 a 08 concluídas.
- Acesso à VPS Hostinger (ou ambiente equivalente).

## Entregáveis
- [ ] Relatório de Benchmark (Tempo Médio de Processamento).
- [ ] Scripts `cron` para limpeza automática de jobs antigos (>30 dias).
- [ ] Documentação de API completa (OpenAPI/Swagger ou Markdown detalhado).
- [ ] Checklist de Go-Live validado.

## Checklist Técnico

### Operação
- [ ] Configurar `logrotate` para evitar disco cheio com logs.
- [ ] Implementar `ArtifactSweeper`: remover arquivos de jobs finalizados há mais de X dias.
- [ ] Validar limites de cgroups ou `ulimit` no systemd para o worker.
- [ ] Criar monitoramento simples (endpoint `/metrics` ou log scrape).

### Testes
- [x] Executar teste de estresse: 100 uploads sequenciais de arquivos variados.
- [ ] Verificar vazamento de memória (Memory Leak) após 12h de operação contínua.
- [ ] Testar rejeição controlada de arquivos acima de 80MB.

### Common
- [x] Garantir que todas as exceções são capturadas e não derrubam o processo principal.
- [ ] Revisar variáveis de ambiente sensíveis (DB_PASSWORD, API_KEY_SALT).

### PDF / Render
- [ ] Validar tempo de renderização em arquivos pesados (max 30s por página).

## Arquivos e módulos impactados
- `scripts/ops/`
- `config/production.json`
- `docs/api/`
- `tests/performance/`

## Critérios de Aceite
- [ ] O sistema processa 20 jobs de 10MB em sequência sem erro e sem OOM.
- [ ] O tempo médio de preflight para arquivos padrão é inferior a 30 segundos.
- [ ] Arquivos antigos são removidos automaticamente pelo script de limpeza.
- [ ] Todos os endpoints respondem em menos de 200ms (exceto upload/download).

## Riscos
- Fragmentação de memória em C++ após muitos jobs.
- CPU throttling da VPS degradando o tempo de processamento em horários de pico.

## Mitigações
- Monitorar `RSS` de memória e forçar reinício do worker se exceder limite de segurança.
- Ajustar a concorrência para 1 job se o throttling for severo.

## Observações de Implementação
- Gerar o log final com o resumo de "Pilot Readiness: GREEN".
- Não deixar logs de debug ativados em produção.

## Definição de pronto
- [ ] código implementado
- [x] build funcionando
- [x] testes mínimos executados
- [ ] critérios de aceite atendidos
- [x] documentação da sprint atualizada

## Status
**Progresso da sprint:** `25%`  
**Situação:** `Em andamento`

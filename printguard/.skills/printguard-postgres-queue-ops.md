# Skill: PrintGuard PostgreSQL Queue Ops

## Missão
Projetar, implementar ou revisar a fila do MVP usando PostgreSQL com baixo risco operacional.

## Escopo
- tabela `jobs`
- polling
- locks
- retries
- requeue
- dead-letter lógica
- worker único ou conservador

## Quando usar
Use esta skill para:
- fila do worker
- lifecycle de jobs
- controle de concorrência
- recuperação após crash

## Regras obrigatórias
1. Não usar RabbitMQ no MVP.
2. Usar PostgreSQL com `SELECT ... FOR UPDATE SKIP LOCKED`.
3. Persistir status de forma transacional.
4. Retry deve ser simples e explícito.
5. Jobs abandonados precisam de estratégia de recuperação.
6. Concorrência deve respeitar a VPS pequena.

## Checklist técnico
- [ ] tabela jobs modelada corretamente
- [ ] polling implementado
- [ ] dequeue transacional implementado
- [ ] `SKIP LOCKED` usado
- [ ] retry with backoff simples
- [ ] requeue após falha controlada
- [ ] timeout de job tratado
- [ ] jobs órfãos recuperáveis
- [ ] limite de concorrência aplicado
- [ ] testes de integração da fila criados

## Política sugerida
- 1 job pesado por vez
- ou 2 leves
- polling a cada 2s quando vazio
- requeue de job preso por heartbeat/timeout
- status claros no banco

## Saída esperada
- fila simples
- confiável
- operável
- sem broker adicional

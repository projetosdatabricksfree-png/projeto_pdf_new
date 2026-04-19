# Skill: PostgreSQL Queue Patterns

## Missão
Usar PostgreSQL como fila do MVP com baixo risco operacional e sem complexidade desnecessária.

## Quando usar
Use esta skill em:
- dequeue
- polling
- retries
- requeue
- detecção de jobs órfãos
- concorrência do worker

## Regras obrigatórias
1. Usar `SELECT ... FOR UPDATE SKIP LOCKED`.
2. Persistir tentativas e timestamps.
3. Diferenciar job queued, running, failed, completed.
4. Implementar retry simples e previsível.
5. Detectar jobs presos.
6. Não simular broker distribuído no banco.

## Padrão recomendado
- polling a cada 2s quando vazio
- lock transacional
- heartbeat ou `updated_at`
- retry com backoff simples
- limite de tentativas
- dead-letter lógica por status

## Checklist técnico
- [ ] dequeue transacional
- [ ] `SKIP LOCKED` aplicado
- [ ] retry simples implementado
- [ ] max attempts definido
- [ ] jobs órfãos detectáveis
- [ ] concorrência limitada
- [ ] testes de integração da fila existem

## Alertas
- Não usar `LISTEN/NOTIFY` como base do MVP se polling simples resolve.
- Não complicar fila com prioridades complexas cedo demais.

## Saída esperada
Fila robusta o suficiente para o MVP, sem broker externo.

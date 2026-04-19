# Skill: spdlog Structured Logging

## Missão
Instrumentar o PrintGuard com logs úteis para operação, debug e auditoria sem poluir a aplicação.

## Quando usar
Use esta skill para:
- logs da API
- logs do worker
- logs de pipeline
- logs de erro
- logs de performance
- correlação por job_id / tenant_id

## Regras obrigatórias
1. Logar contexto útil, não ruído.
2. Incluir `job_id`, `tenant_id` e stage quando aplicável.
3. Diferenciar info, warning e error com rigor.
4. Não logar segredo.
5. Preferir formato estruturado.

## Campos recomendados
- timestamp
- level
- service
- job_id
- tenant_id
- stage
- action
- duration_ms
- message

## Checklist técnico
- [ ] logger inicializado
- [ ] formato estruturado definido
- [ ] contexto por job suportado
- [ ] erro com stack/contexto mínimo
- [ ] logs críticos nos stages do pipeline
- [ ] sem segredo em log

## Alertas
- Não usar log verboso em excesso no hot path.
- Não deixar erro crítico sem contexto mínimo.

## Saída esperada
Logs realmente úteis para operar e depurar o sistema.

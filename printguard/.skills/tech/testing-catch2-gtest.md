# Skill: Testing with Catch2 / GoogleTest

## Missão
Criar testes úteis para o PrintGuard com foco em regras, fixes, pipeline e regressão.

## Quando usar
Use esta skill ao escrever:
- testes unitários
- testes de integração
- golden tests
- benchmarks básicos

## Regras obrigatórias
1. Toda regra nova deve ter teste.
2. Todo fix novo deve ter ao menos um teste de integração.
3. Pipeline principal precisa de smoke tests.
4. Fixtures PDF devem ser pequenas e previsíveis.
5. Não depender só de teste manual.

## Checklist técnico
- [ ] teste unitário de regra criado
- [ ] teste unitário de planner criado
- [ ] teste de integração de fix criado
- [ ] fixture PDF adicionada quando necessário
- [ ] golden expectation definida quando necessário
- [ ] teste de erro/crash path considerado

## Alertas
- Não fazer teste extremamente frágil por detalhe cosmético.
- Não deixar fixture sem documentação do objetivo.

## Saída esperada
Rede de segurança suficiente para evoluir o MVP com confiança.

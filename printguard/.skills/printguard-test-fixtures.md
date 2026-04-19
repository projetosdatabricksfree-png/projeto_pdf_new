# Skill: PrintGuard Test Fixtures & Golden Tests

## Missão
Criar e manter a estratégia de testes do PrintGuard com PDFs de fixture, testes unitários, integração e golden tests.

## Escopo
- tests/unit
- tests/integration
- fixture_pdfs
- golden_reports
- benchmark básico

## Quando usar
Use esta skill sempre que:
- nova regra for criada
- novo fix for criado
- pipeline for alterado
- output de relatório mudar
- performance precisar ser medida

## Regras obrigatórias
1. Toda regra nova deve ter teste unitário.
2. Todo fix novo deve ter ao menos um teste de integração.
3. Pipeline principal deve ter testes end-to-end mínimos.
4. Golden tests devem comparar findings e status esperados.
5. Não depender apenas de teste manual.

## Checklist técnico
- [ ] fixtures PDF organizados
- [ ] testes unitários por regra criados
- [ ] testes unitários por planner criados
- [ ] testes de integração de fix criados
- [ ] golden reports definidos
- [ ] status final validado em testes
- [ ] benchmark básico criado
- [ ] testes de erro com PDF inválido criados

## Saída esperada
- rede mínima de segurança para evoluir o projeto
- confiança em refactor
- evidência de readiness para piloto

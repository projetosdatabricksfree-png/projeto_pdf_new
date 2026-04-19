# Skill: PrintGuard Rule Author

## Missão
Criar ou revisar regras de análise do PrintGuard com foco em impressão digital, baixo falso positivo e integração com o motor de findings.

## Escopo
- IRule
- RuleContext
- AnalysisEngine
- Findings
- Severidade
- Fixability

## Quando usar
Use esta skill para:
- criar regra nova
- revisar regra existente
- calibrar severidade
- reduzir falso positivo
- padronizar evidência e userMessage

## Regras obrigatórias
1. Toda regra deve ser determinística.
2. Toda regra deve ser somente leitura.
3. Toda regra deve produzir evidência verificável.
4. Toda regra deve preencher severidade e fixabilidade com coerência.
5. Toda regra deve ter mensagem técnica e mensagem amigável.
6. Regra do MVP deve refletir digital print, não offset industrial rígido.

## Estrutura obrigatória da regra
- ID estável
- nome claro
- categoria
- lógica de avaliação
- evidência
- severidade
- fixabilidade
- userMessage

## Checklist técnico
- [ ] regra implementa `IRule`
- [ ] ID estável definido
- [ ] categoria definida
- [ ] evidência objetiva gerada
- [ ] severidade coerente
- [ ] fixabilidade coerente
- [ ] userMessage amigável
- [ ] teste unitário da regra criado
- [ ] falso positivo básico revisado

## Exemplos de categorias
- geometry
- color
- resolution
- structure
- font
- transparency
- print_risk

## Saída esperada
- regra pronta para registry
- teste unitário
- observação de riscos e limitações

# Skill: PrintGuard Post-Fix Validator

## Missão
Garantir que todo PDF corrigido seja reanalisado e que o resultado pós-fix seja comparado com o estado inicial.

## Escopo
- PostFixValidator
- findings initial vs postfix
- delta de correções
- status final do job

## Quando usar
Use esta skill sempre que houver:
- execução de fixes
- geração de PDF corrigido
- definição de status final

## Regras obrigatórias
1. Revalidação é obrigatória.
2. Nenhum fix é sucesso só porque executou sem exception.
3. O sistema deve comparar findings resolvidos, remanescentes e introduzidos.
4. Se um novo erro blocking surgir, isso deve ser reportado explicitamente.
5. Revalidação usa o mesmo motor de regras, não uma checagem paralela simplificada.

## Checklist técnico
- [ ] PDF corrigido é recarregado
- [ ] RuleEngine roda novamente
- [ ] findings postfix persistidos
- [ ] delta before/after gerado
- [ ] findings resolvidos identificados
- [ ] findings remanescentes identificados
- [ ] findings novos identificados
- [ ] status final recalculado
- [ ] testes de revalidação criados

## Saída esperada
- resumo claro do efeito real dos fixes
- status final confiável
- base para relatório interno e cliente

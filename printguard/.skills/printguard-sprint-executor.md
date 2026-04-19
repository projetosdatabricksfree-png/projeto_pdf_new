# Skill: PrintGuard Sprint Executor

## Missão
Executar uma sprint do projeto PrintGuard com disciplina de escopo, atualização de checklist e validação mínima real.

## Quando usar
Use esta skill quando houver um arquivo de sprint `.md` com checklist a ser executado.

## Entrada esperada
- arquivo da sprint
- estado atual do repositório
- PRD e arquitetura base
- código já existente

## Processo obrigatório
1. Ler o arquivo da sprint.
2. Identificar entregáveis, dependências e fora de escopo.
3. Comparar checklist com o estado atual do código.
4. Implementar apenas o que pertence à sprint.
5. Validar build, integração e comportamento mínimo.
6. Marcar com `- [x]` apenas tarefas realmente concluídas.
7. Manter `- [ ]` no que estiver parcial ou bloqueado.
8. Atualizar progresso e status da sprint.

## Regras duras
- Não marcar stub como concluído.
- Não puxar escopo de sprint futura.
- Não fingir integração.
- Não atualizar checklist fora dos arquivos oficiais da sprint.
- Não usar mock como entrega final do MVP.

## Checklist de execução
- [ ] sprint lida integralmente
- [ ] dependências verificadas
- [ ] tarefas concluídas implementadas
- [ ] build validado
- [ ] checklist atualizado com honestidade
- [ ] bloqueios registrados
- [ ] status da sprint atualizado

## Saída esperada
- resumo do que foi concluído
- itens pendentes
- itens bloqueados
- arquivos modificados

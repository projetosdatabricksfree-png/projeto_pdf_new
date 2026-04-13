---
name: token-economy
description: >
  Gestão de tokens, uso híbrido de modelos e boas práticas de sessão no Claude Code.
  Use este skill SEMPRE que iniciar um projeto, configurar CLAUDE.md, escolher qual modelo usar
  (Sonnet/Haiku/Opus), trabalhar com MCPs, sub-agentes, Plan Mode, /compact, /clear ou /context.
  Aplique automaticamente em todos os projetos — este skill define o comportamento padrão de
  toda sessão de trabalho.
---

# Token Economy — Uso Híbrido e Gestão de Sessão

Este skill define as práticas obrigatórias de economia de tokens e seleção de modelo para
**todos os projetos**. As regras abaixo devem ser seguidas automaticamente, sem que o usuário
precise lembrar de solicitá-las.

---

## 1. Entenda o Custo Real Antes de Agir

O custo dos tokens é **composto**, não linear.

- Cada mensagem relê **todo** o histórico da conversa desde o início.
- A mensagem 30 pode custar ~180× mais que a mensagem 1.
- Antes de qualquer sessão, a janela de contexto já carrega ~20k tokens de overhead (system prompt, CLAUDE.md, MCPs definidos).
- Um CLAUDE.md de 1.000 linhas ou 3 MCPs conectados elevam o overhead para ~50k tokens **antes do primeiro prompt**.

**Fenômeno Lost in the Middle:** contextos inflados não só custam mais — produzem respostas piores. O modelo presta atenção ao início e ao fim; o meio é ignorado. Você paga pelos tokens do meio sem receber valor deles.

---

## 2. Seleção de Modelo (Uso Híbrido)

Escolha o modelo certo para cada tarefa. Esta é a principal alavanca de custo.

| Modelo | Quando usar | Quando NÃO usar |
|--------|-------------|-----------------|
| **Sonnet** (padrão) | Refatoração, debugging, testes, análise de código, a maioria do trabalho diário | Planejamento arquitetural profundo, raciocínio multi-step complexo |
| **Haiku** (mais barato) | Sub-agentes de busca, formatação, classificação simples, resumos, tarefas auxiliares | Código complexo, debugging difícil, qualquer coisa que exija raciocínio profundo |
| **Opus** (5–10× mais caro) | Decisões arquiteturais críticas, planejamento de longo prazo, análise de trade-offs complexos | Tarefas simples. Use menos de 20% do tempo total |

**Regra prática:** comece sempre com Sonnet. Escale para Opus só se Sonnet não for suficiente. Use Haiku para sub-agentes e tarefas paralelas auxiliares.

---

## 3. Regras de Sessão — Sempre Aplicar

### 3.1 Use `/clear` ao trocar de assunto
Não carregue o contexto do tópico A para uma conversa sobre o tópico B. Cada mensagem em um chat longo é exponencialmente mais cara do que a mesma mensagem em um chat novo. Este único hábito é o principal fator para prolongar a vida de uma sessão.

### 3.2 Execute `/compact` por volta de 60% de capacidade
O autocompact só dispara em ~95%, quando o contexto já está bastante degradado. Não espere. Use `/compact` com instrução explícita do que preservar. Exemplo:
```
/compact Preserva os testes que já passaram, as decisões de arquitetura tomadas e os arquivos que editamos. Descarta o histórico de tentativas que não funcionaram.
```

### 3.3 Use `/context` para monitorar o consumo
Antes de tarefas longas, verifique onde estão indo os tokens: histórico da conversa, overhead de MCPs, arquivos carregados. Torne o invisível visível.

### 3.4 Desconecte MCPs desnecessários
Cada MCP conectado carrega todas as suas definições de ferramentas no contexto a cada mensagem — de forma invisível. Um único servidor pode representar dezenas de milhares de tokens por mensagem. Execute `/mcp` no início de cada sessão e desconecte os que não vai usar.

**Impacto:**
- Sem MCPs: ~5k tokens de overhead por mensagem
- 3 MCPs conectados: ~35k tokens de overhead por mensagem

---

## 4. Comportamento ao Receber Tarefas

### 4.1 Use Plan Mode antes de qualquer tarefa real
Antes de implementar, mapeie a abordagem com Plan Mode (Shift+Tab). Confirme o plano com o usuário antes de qualquer execução. Isso evita a maior fonte de desperdício: seguir pelo caminho errado, escrever código e descartar tudo depois.

```
❌ Sem Plan Mode: prompt → implementa → direção errada → descarta → reimplementa → 2–5× tokens desperdiçados
✅ Com Plan Mode: ativa → mapeia → usuário aprova → executa → zero retrabalho
```

### 4.2 Agrupe perguntas e correções
Três mensagens separadas custam o triplo de uma mensagem combinada. Se o Claude errou algo, edite a mensagem original e regenere — não envie correções como follow-up. Follow-ups acumulam histórico permanentemente; edições substituem a troca inteira.

### 4.3 Seja cirúrgico com referências de arquivos
Não explore o repositório livremente. Use `@nomedoarquivo` para referenciar arquivos específicos. Aponte diretamente para o arquivo e a função relevante — não para o projeto inteiro.

```
❌ Explorativo: "Aqui está o repo. Ache o bug." → lê tudo (+20k tokens)
✅ Cirúrgico: "@src/api.ts linha 45" → lê só o relevante (+1k tokens)
```

### 4.4 Cole só o trecho relevante
Se o problema está em uma função, cole só aquela função. Arquivo inteiro com comentários e docs pode custar ~5.000 tokens; a função relevante custa ~200 tokens.

### 4.5 Observe tarefas longas — não mude de aba
Se o Claude entrar em loop, reler os mesmos arquivos ou seguir pelo caminho errado, pare imediatamente. Tokens gastos num loop não produzem valor.

---

## 5. Estrutura do CLAUDE.md

O CLAUDE.md é lido **uma vez por conversa** (ou após `/clear`), mas seus tokens pesam em **cada mensagem** — porque fazem parte do contexto enviado ao modelo.

### Regras obrigatórias para o CLAUDE.md
- **Menos de 200 linhas** — máximo absoluto
- Funciona como **índice**, não como depósito de instruções
- Armazena: stack, comandos de build, convenções básicas, decisões arquiteturais estáveis
- **Não armazena**: guias completos, checklists detalhados, workflows específicos (esses vão para Skills)
- Aponta para Skills específicos em vez de repetir instruções

### Template de CLAUDE.md enxuto

```markdown
# [Nome do Projeto]

## Stack
- Frontend: [tecnologia]
- Backend: [tecnologia]
- Banco: [tecnologia]

## Comandos
- Dev: `npm run dev`
- Test: `npm test`
- Build: `npm run build`

## Convenções
- Estilo: camelCase, ESM imports
- Commits: conventional commits

## Decisões Arquiteturais
- [Decisão A]: escolhemos X em vez de Y porque Z
- [Decisão B]: ...

## Skills disponíveis
- → skill: pr-review (carrega só ao usar)
- → skill: migrations (carrega só ao usar)
- → skill: deploy-checklist (carrega só ao usar)
```

### O que vai para Skills (não para CLAUDE.md)
Guia completo de PR review, checklist de deploy, padrões de migração de banco, regras de code review, convenções de API, documentação de arquitetura.

### Como o CLAUDE.md deve evoluir

| Fase | Conteúdo | Limite |
|------|----------|--------|
| Início do projeto | Stack, comandos de build, convenções básicas | ~50 linhas |
| Decisões arquiteturais surgem | Registre: "Escolhemos X em vez de Y porque Z" | +algumas linhas |
| Workflows repetitivos aparecem | Crie uma skill — adicione só a referência no CLAUDE.md | 1 linha por skill |
| CLAUDE.md maduro | Fonte da verdade. Cada prompt fica mais curto | < 200 linhas |

**Regra de bolso:** se você vai digitar a mesma instrução mais de 3 vezes, coloque no CLAUDE.md. Se é um workflow específico, crie uma skill.

---

## 6. Multi-Agentes — Use com Critério

Multi-agentes custam **4–10× mais** porque cada sub-agente inicializa do zero com o contexto completo (CLAUDE.md + MCPs + histórico + system prompt).

```
Agente único — 20k tokens de contexto
Multi-agente com 3 sub-agentes — 4 × 20k = 80k tokens, antes de qualquer trabalho real
```

**Quando vale o custo:** tarefas grandes, independentes entre si, onde o paralelismo reduz tempo total significativamente.

**Quando não vale:** qualquer tarefa que um único agente pode fazer em sequência. Não crie agent teams só porque é possível.

**Se usar sub-agentes:** prefira **Haiku** para sub-agentes simples (busca, formatação, classificação).

---

## 7. Checklist de Início de Sessão

Execute mentalmente ao iniciar qualquer sessão de trabalho:

- [ ] MCPs desnecessários desconectados? (`/mcp`)
- [ ] CLAUDE.md com menos de 200 linhas?
- [ ] Tarefa nova e sem relação com a anterior? → `/clear` antes de começar
- [ ] Tarefa complexa? → Ativar Plan Mode antes de implementar
- [ ] Monitorar contexto em tarefas longas → `/context` e `/compact` a ~60%

---

## 8. Resumo das Regras Automáticas

Estas regras se aplicam **sempre**, em todos os projetos, sem necessidade de o usuário solicitar:

1. **Sonnet por padrão** — Haiku para sub-agentes e tarefas auxiliares — Opus com moderação
2. **`/clear` ao trocar de assunto** — não carregue contexto irrelevante
3. **`/compact` a 60%** — não espere o autocompact a 95%
4. **Plan Mode antes de implementar** — confirmar plano antes de executar
5. **Referências cirúrgicas** — `@arquivo:linha`, nunca o repositório inteiro
6. **CLAUDE.md como índice** — máximo 200 linhas, workflows específicos em Skills
7. **MCPs desconectados quando não usados** — overhead invisível e alto
8. **Agrupar prompts** — editar em vez de reenviar correções como follow-up
9. **Observar execuções longas** — interromper loops imediatamente
10. **Multi-agentes apenas quando justificado** — custo multiplica rápido

> **ENCERRADA** — Sprint migrada para `SPRINSTS_REFATORACAO/`. O trabalho realizado aqui foi incorporado ao novo roadmap do MVP comercial. Data de encerramento: 2026-04-19.

---

# Sprint 06 — Engine de Análise MVP

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusão.

## Objetivo
Implementar o coração da triagem técnica do PrintGuard: o motor de regras que analisa o Modelo Canônico do PDF e detecta violações baseadas no Preset e Validation Profile escolhidos.

## Escopo da Sprint
- Implementação do `RuleEngine`.
- Regra de Geometria: Validação de MediaBox vs TrimBox vs Preset.
- Regra de Sangria (Bleed): Checagem se BleedBox é >= 3mm maior que TrimBox.
- Regra de Cor: Detecção de RGB, Spot e Perfis ICC incompatíveis.
- Regra de Resolução (DPI): Triagem de imagens abaixo do limite (ex: 150/300 DPI).
- Regra de Páginas: Validar quantidade de páginas contra o preset (ex: frente e verso).

## Fora do escopo da Sprint
- Aplicação de correções (Fixes).
- Revalidação pós-correção.
- Geração de relatórios complexos.

## Dependências
- Sprints 01 a 05 concluídas.
- Modelo Canônico funcional (S04).

## Entregáveis
- [x] `RuleEngine` capaz de orquestrar múltiplas `IRule`.
- [x] Implementação de 5 regras críticas do MVP.
- [ ] Tabela `findings` populada com os resultados iniciais da análise.

## Checklist Técnico

### Domain
- [ ] Finalizar classe `Finding` com suporte a metadados (page_number, coordinates).

### PDF
- [x] Implementar `ResolutionRule`: vasculhar dicionários de imagens e calcular DPI efetivo (scale vs media).
- [x] Implementar `GeometryRule`: comparar boxes extraídas com dimensões do preset (tolerância de 1mm).
- [x] Implementar `ColorRule`: identificar presença de DeviceRGB ou Perfis ICC indesejados.
- [x] Implementar `BleedRule`: checar integridade entre Trim e Bleed.

### Analysis
- [ ] Criar factory de regras baseada no `ValidationProfile`.
- [x] Implementar execução sequencial (ou paralela leve) das regras.
- [ ] Persistir todos os findings no banco com `phase = 'initial'`.

### Testes
- [ ] Suíte de testes com PDFs "sujos": cores erradas, DPI baixo, sem sangria.
- [ ] Validar falsos positivos em regras de geometria com rotação aplicada.

## Arquivos e módulos impactados
- `src/analysis/`
- `src/pdf/rules/`
- `include/printguard/analysis/`

## Critérios de Aceite
- [x] O sistema detecta imagens abaixo de 150 DPI e gera um Finding de `WARNING` ou `ERROR`.
- [x] O sistema identifica se um arquivo RGB foi enviado para um preset que exige CMYK.
- [ ] Os findings no banco possuem referências de página corretas.
- [ ] O tempo total de análise para um PDF de 10 páginas não excede 5 segundos na VPS.

## Riscos
- Cálculo incorreto de DPI em imagens com transformações complexas (matrizes de translação/escala).
- Excesso de regras tornando o processo lento.

## Mitigações
- Focar nas regras de dicionário primeiro; evitar processamento de stream de pixels se possível.
- Logging de performance por regra para identificar gargalos.

## Observações de Implementação
- Nomes das regras devem seguir o PRD: `PageGeometryRule`, `BleedRule`, `ColorSpaceRule`, `ImageResolutionRule`, `PageCountRule`.
- Findings devem ter códigos persistentes (ex: `PG_ERR_LOW_RES`) para facilitar tradução no relatório.

## Definição de pronto
- [x] código implementado
- [x] build funcionando
- [ ] testes mínimos executados
- [ ] critérios de aceite atendidos
- [x] documentação da sprint atualizada

## Status
**Progresso da sprint:** `60%`  
**Situação:** `Em andamento`

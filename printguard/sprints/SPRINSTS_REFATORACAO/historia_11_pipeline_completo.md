# Historia 11 — Pipeline Completo e Orquestracao

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusao.

## Objetivo

Integrar todas as regras e fixes no pipeline principal (API/Worker e CLI), garantindo o ciclo completo: analyze → fix → revalidate → preview → report.

## Escopo da Historia

- Atualizar JobOrchestrator para ciclo completo
- Atualizar LocalBatchProcessor para novos presets/profiles
- Atualizar ReportBuilder para novos findings/fixes
- Transicoes de estado corretas

## Fora do Escopo

- Implementar regras/fixes novos (ja feito em H04-H09)
- Testes E2E completos (Historia 12)

## Dependencias

- **Historia 10** (FixPlanner dirigido por preset)
- Todas as historias de regras e fixes (H04-H09) devem estar concluidas

## Skill correspondente

`historia-11-pipeline-completo.md`

## Checklist Tecnico

### JobOrchestrator

- [ ] Atualizar `run_pipeline()` para executar ciclo completo:
  1. [ ] Carregar PDF → `PdfLoader` → `DocumentModel`
  2. [ ] Analisar → `RuleEngine::run()` com todas as regras registradas
  3. [ ] Planejar fixes → `FixPlanner::build_plan()` usando preset.fix_policy
  4. [ ] Executar fixes → `FixEngine::execute()` com todos os fixes registrados
  5. [ ] Revalidar → `RuleEngine::run()` no PDF corrigido
  6. [ ] Comparar findings pre/pos fix → `RevalidationDelta`
  7. [ ] Renderizar preview → `PreviewRenderer`
  8. [ ] Gerar relatorios → `ReportBuilder`
  9. [ ] Atualizar status do job baseado no resultado
- [ ] Transicoes de estado: `uploaded → processing → analyzing → fixing → revalidating → completed|manual_review_required|failed`

### LocalBatchProcessor

- [ ] Atualizar `process_file()` para usar novos presets expandidos
- [ ] Atualizar `select_preset()` para funcionar com 32 presets em subdiretorios
- [ ] Suportar selecao de profile pelo CLI (parametro adicional)
- [ ] Usar preset.fix_policy para decidir fixes
- [ ] Gerar relatorio completo com todos os novos findings/fixes

### ReportBuilder

- [ ] Atualizar relatorio tecnico para incluir:
  - [ ] Todos os novos finding codes (TAC, output intent, overprint, black, annotations, layers, spot, rotation)
  - [ ] Todos os novos fix records
  - [ ] `preset.family` no relatorio
  - [ ] `manual_review_reasons` quando aplicavel
- [ ] Atualizar relatorio cliente para incluir:
  - [ ] Descricao amigavel de cada novo fix aplicado
  - [ ] Explicacao clara do que ficou para revisao manual e porque
  - [ ] Lista de recomendacoes especificas por familia de produto
- [ ] Atualizar resumo markdown

### Testes de Integracao

- [ ] Teste: CLI processa PDF com preset `business_card_90x50` e profile `digital_print_standard`
- [ ] Teste: CLI processa PDF com preset `tcc_a4` e profile `books_and_documents`
- [ ] Teste: Pipeline completo gera relatorio tecnico + cliente + resumo
- [ ] Teste: PDF com RGB gera finding → fix → revalidacao mostra finding resolvido
- [ ] Compilacao limpa

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `src/orchestration/orchestrator.cpp` | Ciclo completo |
| `src/orchestration/local_batch_processor.cpp` | Novos presets/profiles |
| `include/printguard/orchestration/local_batch_processor.hpp` | Parametro profile |
| `src/report/report_builder.cpp` | Novos findings/fixes |
| `apps/cli/main.cpp` | Parametro profile |

## Criterios de Aceite

- [ ] Pipeline completo funciona de ponta a ponta
- [ ] Presets de todas as 4 familias funcionam corretamente
- [ ] Relatorios refletem todos os findings e fixes
- [ ] Status final correto (completed, manual_review, failed)
- [ ] Compilacao limpa

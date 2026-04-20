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

- [x] Atualizar `run_pipeline()` para executar ciclo completo:
  1. [x] Carregar PDF → `PdfLoader` → `DocumentModel`
  2. [x] Analisar → `RuleEngine::run()` com todas as regras registradas
  3. [x] Planejar fixes → `FixPlanner::build_plan()` usando preset.fix_policy
  4. [x] Executar fixes → `FixEngine::execute()` com todos os fixes registrados
  5. [x] Revalidar → `RuleEngine::run()` no PDF corrigido
  6. [x] Comparar findings pre/pos fix → `RevalidationDelta`
  7. [x] Renderizar preview → `PreviewRenderer`
  8. [x] Gerar relatorios → `ReportBuilder`
  9. [x] Atualizar status do job baseado no resultado
- [x] Transicoes de estado: `uploaded → processing → analyzing → fixing → revalidating → completed|manual_review_required|failed`
  - Estado atual: implementado em codigo e compilando. A suite automatizada da H11 validou o fluxo completo via CLI/`LocalBatchProcessor`; o caminho completo com DB/storage do worker nao ganhou teste automatizado dedicado nesta historia.

### LocalBatchProcessor

- [x] Atualizar `process_file()` para usar novos presets expandidos
- [x] Atualizar `select_preset()` para funcionar com 32 presets em subdiretorios
- [x] Suportar selecao de profile pelo CLI (parametro adicional)
- [x] Usar preset.fix_policy para decidir fixes
- [x] Gerar relatorio completo com todos os novos findings/fixes

### ReportBuilder

- [x] Atualizar relatorio tecnico para incluir:
  - [x] Todos os novos finding codes (TAC, output intent, overprint, black, annotations, layers, spot, rotation)
  - [x] Todos os novos fix records
  - [x] `preset.family` no relatorio
  - [x] `manual_review_reasons` quando aplicavel
- [x] Atualizar relatorio cliente para incluir:
  - [x] Descricao amigavel de cada novo fix aplicado
  - [x] Explicacao clara do que ficou para revisao manual e porque
  - [x] Lista de recomendacoes especificas por familia de produto
- [x] Atualizar resumo markdown

### Testes de Integracao

- [x] Teste: CLI processa PDF com preset `business_card_90x50` e profile `digital_print_standard`
- [x] Teste: CLI processa PDF com preset `tcc_a4` e profile `books_and_documents`
- [x] Teste: Pipeline completo gera relatorio tecnico + cliente + resumo
- [x] Teste: PDF com RGB gera finding → fix → revalidacao mostra finding resolvido
- [x] Compilacao limpa

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `include/printguard/domain/job.hpp` | Novos status de pipeline |
| `include/printguard/orchestration/orchestrator.hpp` | Construtor com presets/profiles + reuse do batch |
| `src/orchestration/orchestrator.cpp` | Ciclo completo |
| `include/printguard/orchestration/local_batch_processor.hpp` | Contrato do resultado + `process_file()` publico |
| `src/orchestration/local_batch_processor.cpp` | Novos presets/profiles |
| `src/report/report_builder.cpp` | Novos findings/fixes |
| `apps/cli/main.cpp` | Parametro profile |
| `apps/api/main.cpp` | Injecao de presets/profiles no orchestrator |
| `apps/worker/main.cpp` | Injecao de presets/profiles no orchestrator |
| `src/storage/local_storage.cpp` | Persistencia com extensoes corretas por artefato |
| `tests/unit/historia_11_pipeline_completo_test.cpp` | Suite hermetica da H11 |
| `tests/CMakeLists.txt` | Registro da suite H11 e dependencia da CLI |

## Criterios de Aceite

- [x] Pipeline completo funciona de ponta a ponta
- [ ] Presets de todas as 4 familias funcionam corretamente
  - Estado atual: carregamento recursivo dos 32 presets em subdiretorios esta validado e o fluxo automatizado foi exercitado para `quick_print` e `documents_and_books`. As familias `signage_and_large_format` e `labels_and_stickers` ainda nao receberam teste automatizado dedicado na H11.
- [x] Relatorios refletem todos os findings e fixes
- [x] Status final correto (completed, manual_review, failed)
- [x] Compilacao limpa

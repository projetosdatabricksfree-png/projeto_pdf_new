# Skill: Historia 11 — Pipeline Completo e Orquestracao

## Missao

Integrar todas as regras e fixes no pipeline principal, garantindo o ciclo completo: analyze → fix → revalidate → preview → report.

## Sprint correspondente

`sprints/SPRINSTS_REFATORACAO/historia_11_pipeline_completo.md`

## Quando usar

Use esta skill para:
- atualizar JobOrchestrator para ciclo completo
- atualizar LocalBatchProcessor para novos presets/profiles
- atualizar ReportBuilder para novos findings/fixes
- garantir transicoes de estado corretas

## Regras obrigatorias

1. Pipeline completo: analyze → fix → revalidate → preview → report.
2. Revalidacao obrigatoria apos qualquer fix.
3. Nunca sobrescrever original.
4. Status final baseado no resultado do FixPlanner (completed, manual_review, failed).
5. Relatorio tecnico deve listar TODOS os findings e fixes.
6. Relatorio cliente deve explicar em linguagem simples.

## Ciclo do Pipeline

1. Carregar PDF → PdfLoader → DocumentModel
2. Analisar → RuleEngine::run() com TODAS as regras
3. Planejar fixes → FixPlanner::build_plan() usando preset.fix_policy
4. Executar fixes → FixEngine::execute()
5. Revalidar → RuleEngine::run() no PDF corrigido
6. Comparar pre/pos → RevalidationDelta
7. Renderizar preview → PreviewRenderer
8. Gerar relatorios → ReportBuilder
9. Atualizar status do job

## Checklist de saida

- [ ] Pipeline completo funciona
- [ ] Presets de todas as familias funcionam
- [ ] Relatorios completos
- [ ] Status final correto
- [ ] Compilacao limpa

# Historia 10 — FixPlanner Dirigido por Preset/Profile

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusao.

## Objetivo

Refatorar o `FixPlanner` para usar `preset.fix_policy` e `preset.manual_review_policy` em vez de logica hardcoded. O planner deve ser 100% dirigido por dados declarativos.

## Escopo da Historia

- Refatorar `FixPlanner::build_plan()` para consultar fix_policy do preset
- Implementar logica de manual_review baseada no preset
- Eliminar todos os hardcodes de finding codes no planner

## Fora do Escopo

- Criar novos fixes (Historias 07-09)
- Alterar pipeline (Historia 11)

## Dependencias

- **Historias 07-09** (todos os fixes registrados)
- **Historia 01** (preset com fix_policy e manual_review_policy)

## Skill correspondente

`historia-10-fix-planner-preset.md`

## Regra critica

**O FixPlanner NAO deve tomar decisoes por conta propria.** Toda decisao de "corrigir ou nao" vem do `preset.fix_policy`. Toda decisao de "revisao manual" vem do `preset.manual_review_policy`.

## Checklist Tecnico

### Refatorar FixPlanner

- [x] Remover mapeamento hardcoded de finding codes → fixes
- [x] Novo fluxo de `build_plan()`:
  - [x] Para cada finding com fixability AUTOMATIC_SAFE:
    - [x] Consultar qual IFix trata esse finding code (via `IFix::targets_finding_code()`)
    - [x] Consultar `preset.fix_policy` para verificar se o fix esta habilitado:
      - [x] `PG_ERR_RGB_COLORSPACE` → `fix_policy.auto_fix_rgb_to_cmyk`
      - [x] `PG_ERR_MISSING_BLEED_BOX` → `fix_policy.auto_normalize_boxes`
      - [x] `PG_ERR_MISSING_OUTPUT_INTENT` → `fix_policy.auto_attach_output_intent`
      - [x] `PG_ERR_TAC_EXCEEDED` → `fix_policy.auto_reduce_tac`
      - [x] `PG_ERR_WHITE_OVERPRINT` → `fix_policy.auto_remove_white_overprint`
      - [x] `PG_WARN_RICH_BLACK_TEXT` → `fix_policy.auto_normalize_black`
      - [x] `PG_WARN_ANNOTATIONS` → `fix_policy.auto_remove_annotations`
      - [x] `PG_WARN_LAYERS_PRESENT` → `fix_policy.auto_remove_layers_when_safe`
      - [x] `PG_WARN_SPOT_COLORS` → `fix_policy.auto_fix_spot_to_cmyk`
      - [x] `PG_WARN_ROTATION_MISMATCH` → `fix_policy.auto_rotate_pages`
    - [x] Se habilitado: adicionar ao plano
    - [x] Se desabilitado: adicionar a `skipped_fixes` com motivo

### Logica de Manual Review

- [x] Apos construir o plano, avaliar findings nao resolvidos:
  - [x] Se finding tem severity ERROR e nao ha fix disponivel ou fix desabilitado → `manual_review_required`
  - [x] Consultar `manual_review_policy` para findings especificos:
    - [x] `PG_ERR_SAFETY_MARGIN` → `manual_review_on_safety_margin_violation`
    - [x] bleed visual ausente → `manual_review_on_visual_bleed_missing`
    - [x] transparencia complexa → `manual_review_on_complex_transparency`
    - [ ] fonte nao embutida → `manual_review_on_font_embedding_issue`
      - Estado atual: hook declarativo implementado no planner para `PG_ERR_FONT_NOT_EMBEDDED`, mas ainda nao existe regra produtora desse finding no repositório.
    - [x] resolucao abaixo do minimo → `manual_review_on_low_resolution_below_error`
- [x] Resultado do plano: `needs_manual_review` boolean + `manual_review_reasons` lista

### Status Final

- [x] Definir logica clara de status final baseada no plano:
  - [x] Todos os findings resolvidos → `completed`
  - [x] Alguns findings nao resolvidos mas nenhum blocking → `completed` (com warnings)
  - [x] Findings blocking nao resolvidos + manual_review → `manual_review_required`
  - [x] Erro no pipeline → `failed`

### Testes

- [x] Teste: preset com `auto_fix_rgb_to_cmyk: false` NAO inclui fix de cor no plano
- [x] Teste: preset com `auto_fix_rgb_to_cmyk: true` INCLUI fix de cor no plano
- [x] Teste: finding blocking sem fix → `manual_review_required`
- [x] Teste: preset documental (bleed 0) nao gera manual_review por bleed
- [x] Teste: `manual_review_policy` e respeitada corretamente
- [x] Compilacao limpa

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `include/printguard/fix/fix_engine.hpp` | Atualizar FixPlan com manual_review |
| `src/fix/fix_engine.cpp` | Refatorar build_plan() |
| `src/orchestration/local_batch_processor.cpp` | Passar preset para o planner |
| `tests/unit/historia_10_fix_planner_preset_test.cpp` | Cobertura da H10 |

## Criterios de Aceite

- [x] Nenhum hardcode de finding code no FixPlanner
- [x] Todas as decisoes vem do preset/profile
- [x] Manual review funciona corretamente por familia de produto
- [x] Compilacao limpa

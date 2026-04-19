# Skill: Historia 10 — FixPlanner Dirigido por Preset/Profile

## Missao

Refatorar o FixPlanner para ser 100% dirigido por dados declarativos do preset (fix_policy, manual_review_policy). Eliminar todos os hardcodes.

## Sprint correspondente

`sprints/SPRINSTS_REFATORACAO/historia_10_fix_planner_preset.md`

## Quando usar

Use esta skill para:
- refatorar FixPlanner::build_plan()
- implementar logica de manual_review baseada no preset
- eliminar hardcodes de finding codes

## Regra critica

**O FixPlanner NAO deve tomar decisoes por conta propria.** Toda decisao vem do preset.fix_policy e preset.manual_review_policy.

## Regras obrigatorias

1. Nenhum hardcode de finding code no FixPlanner.
2. Cada IFix declara targets_finding_code() — planner consulta fix_policy para verificar se esta habilitado.
3. manual_review_policy determina quando mandar para revisao manual.
4. Status final: completed | manual_review_required | failed.
5. preset com fix desabilitado = fix NAO e aplicado.

## Mapeamento fix_policy → finding code

| fix_policy campo | Finding code |
|---|---|
| auto_fix_rgb_to_cmyk | PG_ERR_RGB_COLORSPACE |
| auto_fix_spot_to_cmyk | PG_WARN_SPOT_COLORS |
| auto_attach_output_intent | PG_ERR_MISSING_OUTPUT_INTENT |
| auto_normalize_boxes | PG_ERR_MISSING_BLEED_BOX |
| auto_rotate_pages | PG_WARN_ROTATION_MISMATCH |
| auto_remove_white_overprint | PG_ERR_WHITE_OVERPRINT |
| auto_remove_annotations | PG_WARN_ANNOTATIONS |
| auto_remove_layers_when_safe | PG_WARN_LAYERS_PRESENT |
| auto_reduce_tac | PG_ERR_TAC_EXCEEDED |
| auto_normalize_black | PG_WARN_RICH_BLACK_TEXT |

## Checklist de saida

- [ ] FixPlanner sem hardcodes
- [ ] fix_policy respeitada
- [ ] manual_review_policy respeitada
- [ ] Testes com presets diferentes
- [ ] Compilacao limpa

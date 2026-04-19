# Skill: Historia 06 — Regras Complementares: Annotations, Layers, SpotColor, Rotacao

## Missao

Implementar 4 regras complementares de analise para deteccao de annotations, layers, spot colors e rotacao incorreta.

## Sprint correspondente

`sprints/SPRINSTS_REFATORACAO/historia_06_regras_complementares.md`

## Quando usar

Use esta skill para:
- implementar AnnotationRule
- implementar LayerRule
- implementar SpotColorRule
- implementar RotationRule

## Regras obrigatorias

1. Toda regra implementa IRule.
2. AnnotationRule deve preservar links (/Link) — apenas detectar nao-links.
3. LayerRule deve verificar /OCProperties no catalogo.
4. SpotColorRule deve respeitar preset.color_policy.allow_spot_colors.
5. RotationRule deve respeitar preset.orientation ("either" = nao gerar finding).
6. Mensagens em portugues.

## Finding codes e severidades

| Regra | Finding Code | Severity | Fixability |
|---|---|---|---|
| AnnotationRule | PG_WARN_ANNOTATIONS | WARNING | AUTOMATIC_SAFE |
| LayerRule | PG_WARN_LAYERS_PRESENT | WARNING | AUTOMATIC_SAFE |
| SpotColorRule | PG_WARN_SPOT_COLORS | WARNING | AUTOMATIC_SAFE |
| RotationRule | PG_WARN_ROTATION_MISMATCH | WARNING | AUTOMATIC_SAFE |

## Checklist de saida

- [ ] 4 regras implementadas
- [ ] Registradas no RuleEngine
- [ ] Ativadas nos profiles
- [ ] Testes unitarios
- [ ] Compilacao limpa

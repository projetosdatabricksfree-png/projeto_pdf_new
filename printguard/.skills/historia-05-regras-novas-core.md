# Skill: Historia 05 — Regras Novas Core: TAC, OutputIntent, Overprint, Preto

## Missao

Implementar as 4 regras de analise mais criticas para o MVP comercial, usando a arquitetura IRule.

## Sprint correspondente

`sprints/SPRINSTS_REFATORACAO/historia_05_regras_novas_core.md`

## Quando usar

Use esta skill para:
- implementar TacRule
- implementar OutputIntentRule
- implementar WhiteOverprintRule
- implementar BlackConsistencyRule
- atualizar SafetyMarginRule

## Regras obrigatorias

1. Toda regra implementa IRule.
2. Toda regra deve produzir evidence verificavel.
3. Toda regra deve ter mensagem tecnica e mensagem amigavel (em portugues).
4. Thresholds vem do preset/profile, NUNCA hardcoded.
5. TacRule deve usar amostragem para nao saturar CPU (ex: cada 10a linha de pixel).
6. Regras nao devem modificar o PDF — somente leitura.

## Finding codes e severidades

| Regra | Finding Code | Severity | Fixability |
|---|---|---|---|
| TacRule | PG_ERR_TAC_EXCEEDED | ERROR | AUTOMATIC_SAFE |
| TacRule | PG_WARN_TAC_HIGH | WARNING | NONE |
| OutputIntentRule | PG_ERR_MISSING_OUTPUT_INTENT | ERROR | AUTOMATIC_SAFE |
| WhiteOverprintRule | PG_ERR_WHITE_OVERPRINT | ERROR | AUTOMATIC_SAFE |
| BlackConsistencyRule | PG_WARN_RICH_BLACK_TEXT | WARNING | AUTOMATIC_SAFE |

## Checklist de saida

- [ ] 4 regras implementadas
- [ ] SafetyMarginRule usa preset.safe_margin_mm
- [ ] Registradas no RuleEngine
- [ ] Ativadas nos profiles
- [ ] Testes unitarios
- [ ] Compilacao limpa

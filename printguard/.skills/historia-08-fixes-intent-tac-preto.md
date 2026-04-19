# Skill: Historia 08 — Fixes: OutputIntent, TAC Reduction, Black Normalization

## Missao

Implementar 3 fixes criticos: attachment de Output Intent CMYK, reducao de TAC, e normalizacao de preto em texto.

## Sprint correspondente

`sprints/SPRINSTS_REFATORACAO/historia_08_fixes_intent_tac_preto.md`

## Quando usar

Use esta skill para:
- implementar AttachOutputIntentFix
- implementar TacReductionFix
- implementar BlackNormalizationFix

## Regras obrigatorias

1. Todo fix implementa IFix.
2. AttachOutputIntentFix deve ler perfil ICC de preset.color_policy.output_intent_profile.
3. TacReductionFix deve usar preset.max_total_ink_percent como teto.
4. TacReductionFix reduz CMY proporcionalmente preservando K.
5. BlackNormalizationFix so atua em blocos de texto (BT..ET), NAO em graficos.
6. Preto seguro = `0 0 0 1 k` (pure K black).
7. PDF resultante DEVE ser validado.

## Logica do TacReductionFix

Para cada pixel CMYK com TAC > max_tac:
```
excess = (C + M + Y + K) - max_tac
if (C + M + Y) > 0:
    ratio = (max_tac - K) / (C + M + Y)
    C_new = C * ratio
    M_new = M * ratio
    Y_new = Y * ratio
```

## Checklist de saida

- [ ] AttachOutputIntentFix implementado
- [ ] TacReductionFix implementado
- [ ] BlackNormalizationFix implementado
- [ ] Registrados no FixEngine
- [ ] Testes
- [ ] Compilacao limpa

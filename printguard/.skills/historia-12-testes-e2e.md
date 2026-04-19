# Skill: Historia 12 — Testes E2E e Validacao Final

## Missao

Criar suite completa de testes end-to-end cobrindo todos os cenarios do MVP comercial.

## Sprint correspondente

`sprints/SPRINSTS_REFATORACAO/historia_12_testes_e2e.md`

## Quando usar

Use esta skill para:
- criar PDFs de teste para cada cenario
- implementar testes E2E do pipeline completo
- validar cada familia de produto
- validar cada profile
- documentar resultados

## Regras obrigatorias

1. Cada cenario principal deve ter pelo menos 1 PDF de teste.
2. Testes devem cobrir o pipeline completo: analyze → fix → revalidate → report.
3. Cada familia de produto deve ter pelo menos 1 teste E2E.
4. Cada profile deve ter pelo menos 1 teste E2E.
5. PDF conforme (passthrough) DEVE gerar 0 findings.
6. PDFs corrigidos DEVEM ser validos (QPDF check).

## Cenarios de teste obrigatorios

| Cenario | PDF | O que testa |
|---|---|---|
| RGB image | rgb_image.pdf | ImageColorConvertFix |
| RGB operators | rgb_operators.pdf | ConvertRgbToCmykFix |
| TAC exceeded | tac_exceeded.pdf | TacRule + TacReductionFix |
| No output intent | no_output_intent.pdf | OutputIntentRule + AttachOutputIntentFix |
| White overprint | white_overprint.pdf | WhiteOverprintRule + RemoveWhiteOverprintFix |
| Rich black text | rich_black_text.pdf | BlackConsistencyRule + BlackNormalizationFix |
| Annotations | with_annotations.pdf | AnnotationRule + RemoveAnnotationsFix |
| Layers | with_layers.pdf | LayerRule + FlattenLayersFix |
| Spot colors | spot_colors.pdf | SpotColorRule + SpotColorConversionFix |
| Rotation | wrong_rotation.pdf | RotationRule + RotationFix |
| Conformant | conformant.pdf | Passthrough |
| Multiple issues | multiple_issues.pdf | Multiplos fixes |

## Checklist de saida

- [ ] PDFs de teste criados
- [ ] Testes E2E por cenario
- [ ] Testes por familia
- [ ] Testes por profile
- [ ] PDFs validos apos fix
- [ ] Documentacao de resultados
- [ ] Compilacao limpa

# Skill: Historia 09 — Fixes de Limpeza: Overprint, Annotations, Layers, SpotColor, Rotacao

## Missao

Implementar 5 fixes de limpeza e normalizacao do PDF.

## Sprint correspondente

`sprints/SPRINSTS_REFATORACAO/historia_09_fixes_limpeza.md`

## Quando usar

Use esta skill para:
- implementar RemoveWhiteOverprintFix
- implementar RemoveAnnotationsFix
- implementar FlattenLayersFix
- implementar SpotColorConversionFix
- implementar RotationFix

## Regras obrigatorias

1. Todo fix implementa IFix.
2. RemoveAnnotationsFix DEVE preservar /Link (links podem ser uteis).
3. FlattenLayersFix apenas remove metadados de OCG, NAO rasteriza conteudo.
4. SpotColorConversionFix trata apenas caso simples (AlternateSpace = CMYK). Casos complexos: skip.
5. RotationFix ajusta /Rotate, NAO transforma conteudo da pagina.
6. RotationFix so atua quando preset.orientation != "either".

## Checklist de saida

- [ ] 5 fixes implementados
- [ ] Registrados no FixEngine
- [ ] Fixes respeitam limites de seguranca
- [ ] Testes
- [ ] Compilacao limpa

# Skill: PrintGuard Preview Performance

## Missão
Implementar ou revisar o módulo de preview sem transformar renderização em gargalo da VPS.

## Escopo
- preview da primeira página
- overlay visual
- timeout
- controle de resolução
- render CPU-bound

## Quando usar
Use esta skill para:
- `PreviewRenderer`
- `PageRasterizer`
- `OverlayDrawer`
- políticas de preview

## Regras obrigatórias
1. Preview do MVP é enxuto.
2. Primeira página por padrão.
3. Timeout obrigatório.
4. Falha no preview não deve invalidar o job inteiro sem necessidade.
5. Não renderizar documento completo por padrão.
6. Não usar GPU.
7. Não explodir RAM nem CPU.

## Checklist técnico
- [ ] render da página 1 implementado
- [ ] largura máxima controlada
- [ ] compressão JPEG definida
- [ ] overlay opcional implementado
- [ ] timeout de preview respeitado
- [ ] fallback sem preview existe
- [ ] preview salvo como artefato
- [ ] teste com PDF simples executado
- [ ] custo computacional revisado

## Parâmetros sugeridos
- página padrão: 0
- largura máxima: 1200 px
- JPEG quality: 80-85
- preview opcional por config
- overlay leve

## Saída esperada
- preview útil para UX
- custo operacional aceitável
- comportamento previsível em PDFs pesados

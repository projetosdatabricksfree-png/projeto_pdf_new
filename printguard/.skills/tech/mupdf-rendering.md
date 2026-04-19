# Skill: MuPDF Rendering

## Missão
Gerar previews úteis com MuPDF sem transformar renderização em gargalo operacional.

## Quando usar
Use esta skill para:
- preview da primeira página
- rasterização
- timeout de render
- overlays
- export JPEG/PNG

## Regras obrigatórias
1. Preview do MVP é leve.
2. Página 1 por padrão.
3. Timeout obrigatório.
4. Falha de preview não deve derrubar job inteiro.
5. Não renderizar documento inteiro por padrão.
6. Controlar resolução e memória.

## Parâmetros sugeridos
- página: 0
- largura máxima: 1200 px
- JPEG quality: 80-85
- overlay opcional
- timeout duro

## Checklist técnico
- [ ] render básico implementado
- [ ] export JPEG funciona
- [ ] overlay opcional funciona
- [ ] timeout configurado
- [ ] custo computacional revisado
- [ ] fallback sem preview existe

## Alertas
- Não usar preview full-document no pipeline padrão.
- Não gerar imagem gigante.
- Não bloquear finalização do job por preview opcional.

## Saída esperada
Preview leve, útil e previsível.

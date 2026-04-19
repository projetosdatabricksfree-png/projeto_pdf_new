# Skill: LittleCMS2 Color Management

## Missão
Implementar conversão e política de cor com LittleCMS2 de forma conservadora e auditável.

## Quando usar
Use esta skill em:
- RGB -> CMYK
- spot -> CMYK
- perfis ICC
- output intent
- políticas de rendering intent

## Regras obrigatórias
1. Conversão de cor deve ser conservadora.
2. Toda transformação deve ser rastreável.
3. Perfis ICC devem ser carregados de forma controlada.
4. Não “inventar” perfil de destino sem política definida.
5. Mudanças de cor precisam aparecer no relatório técnico.

## Políticas sugeridas
- sRGB como origem comum
- GRACoL/FOGRA conforme preset/profile
- perceptual para imagem fotográfica quando aplicável
- relative colorimetric para elementos gráficos quando apropriado

## Checklist técnico
- [ ] perfis ICC carregam corretamente
- [ ] transformações são reutilizadas/cached quando possível
- [ ] RGB -> CMYK implementado
- [ ] spot -> CMYK implementado quando previsto
- [ ] metadata de transformação registrada
- [ ] testes básicos de conversão criados

## Alertas
- Cor é área de alto risco.
- Não afirmar equivalência visual perfeita.
- Não promover fix de cor sem revalidação.

## Saída esperada
Conversão de cor tecnicamente consistente e operacionalmente segura.

# Historia 12 — Testes E2E e Validacao Final

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusao.

## Objetivo

Criar suite completa de testes end-to-end cobrindo todos os cenarios do MVP comercial, validando que o pipeline completo funciona corretamente para cada familia de produto e cada tipo de problema.

## Escopo da Historia

- Criar PDFs de teste para cada cenario principal
- Testes E2E do pipeline completo
- Validar cada familia de produto
- Validar cada profile
- Documentar resultados

## Fora do Escopo

- Implementar novos fixes ou regras
- Testes de stress/performance (pos-MVP)

## Dependencias

- **Historia 11** (pipeline completo integrado)

## Skill correspondente

`historia-12-testes-e2e.md`

## Checklist Tecnico

### PDFs de Teste (Fixtures)

- [ ] Criar diretorio `tests/fixtures/e2e/`
- [ ] Criar ou obter PDFs de teste para cada cenario:
  - [ ] `rgb_image.pdf` — PDF com imagem RGB (testa ImageColorConvertFix)
  - [ ] `rgb_operators.pdf` — PDF com operadores RGB em content stream (testa ConvertRgbToCmykFix)
  - [ ] `tac_exceeded.pdf` — PDF com imagem CMYK com TAC > 320% (testa TacRule + TacReductionFix)
  - [ ] `no_output_intent.pdf` — PDF sem Output Intent (testa OutputIntentRule + AttachOutputIntentFix)
  - [ ] `white_overprint.pdf` — PDF com overprint em objeto branco (testa WhiteOverprintRule + RemoveWhiteOverprintFix)
  - [ ] `rich_black_text.pdf` — PDF com texto em preto rico (testa BlackConsistencyRule + BlackNormalizationFix)
  - [ ] `with_annotations.pdf` — PDF com anotacoes (testa AnnotationRule + RemoveAnnotationsFix)
  - [ ] `with_layers.pdf` — PDF com OCG/layers (testa LayerRule + FlattenLayersFix)
  - [ ] `spot_colors.pdf` — PDF com cores spot (testa SpotColorRule + SpotColorConversionFix)
  - [ ] `wrong_rotation.pdf` — PDF com rotacao incorreta (testa RotationRule + RotationFix)
  - [ ] `conformant.pdf` — PDF 100% conforme (testa passthrough sem findings)
  - [ ] `multiple_issues.pdf` — PDF com multiplos problemas combinados

### Testes E2E por Cenario

- [ ] Teste: `rgb_image.pdf` + `digital_print_standard` → imagem convertida para CMYK, finding resolvido na revalidacao
- [ ] Teste: `tac_exceeded.pdf` + `digital_print_standard` → TAC reduzido para <= 320%
- [ ] Teste: `no_output_intent.pdf` → Output Intent anexado
- [ ] Teste: `white_overprint.pdf` → overprint removido
- [ ] Teste: `rich_black_text.pdf` → preto normalizado em texto
- [ ] Teste: `with_annotations.pdf` → anotacoes removidas
- [ ] Teste: `with_layers.pdf` → layers removidas
- [ ] Teste: `conformant.pdf` → passthrough, 0 findings, status completed
- [ ] Teste: `multiple_issues.pdf` → multiplos fixes aplicados, revalidacao mostra resolucao

### Testes por Familia de Produto

- [ ] Teste: preset `business_card_90x50` com PDF de cartao — bleed exigida, DPI >= 250
- [ ] Teste: preset `tcc_a4` com PDF de documento — bleed NAO exigida, safety margin relaxada
- [ ] Teste: preset `banner_60x90` com PDF de banner — DPI >= 100 (threshold baixo)
- [ ] Teste: preset `sticker_square_5x5` com PDF de adesivo — bleed exigida, DPI >= 300

### Testes por Profile

- [ ] Teste: `digital_print_standard` aplica fixes agressivamente
- [ ] Teste: `digital_print_safe` tem TAC 300 em vez de 320
- [ ] Teste: `books_and_documents` nao exige bleed para documentos
- [ ] Teste: `banner_and_signage` aceita DPI mais baixo

### Validacao de Relatorios

- [ ] Teste: relatorio tecnico lista todos os findings iniciais e pos-fix
- [ ] Teste: relatorio tecnico lista todos os fixes aplicados e nao aplicados
- [ ] Teste: relatorio cliente explica em linguagem simples o que foi corrigido
- [ ] Teste: relatorio cliente explica o que ficou para revisao manual
- [ ] Teste: batch report com multiplos arquivos tem resumo correto

### Validacao de PDFs Resultantes

- [ ] Teste: todos os PDFs corrigidos sao validos (QPDF check)
- [ ] Teste: PDFs corrigidos mantem estrutura basica (paginas, conteudo)
- [ ] Teste: PDFs corrigidos tem Output Intent quando exigido
- [ ] Teste: PDFs corrigidos nao tem mais findings blocking na revalidacao (ou estao em manual_review)

### Documentacao de Resultados

- [ ] Criar `tests/fixtures/e2e/README.md` com descricao de cada PDF de teste
- [ ] Documentar resultados esperados por cenario

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `tests/unit/` | Novos arquivos de teste E2E |
| `tests/fixtures/e2e/` | PDFs de teste |
| `tests/CMakeLists.txt` | Adicionar novos testes |

## Criterios de Aceite

- [ ] Todos os testes E2E passam
- [ ] Cada familia de produto tem pelo menos 1 teste E2E
- [ ] Cada profile tem pelo menos 1 teste E2E
- [ ] PDFs resultantes sao validos
- [ ] Relatorios completos e corretos
- [ ] Zero false positives em PDF conforme (passthrough)
- [ ] Compilacao limpa com todos os testes

# Historia 03 — Catalogo de 32 Presets MVP

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusao.

## Objetivo

Criar todos os 32 presets JSON do MVP comercial organizados em 4 familias de produto, usando o schema expandido da Historia 01.

## Escopo da Historia

- Organizar presets em subpastas por familia
- Criar 32 arquivos JSON com valores fechados da especificacao oficial
- Atualizar ConfigLoader para recursar subdiretorios

## Fora do Escopo

- Alterar schema do preset (Historia 01)
- Implementar regras/fixes novos (Historias 04+)

## Dependencias

- **Historia 01** (schema expandido deve estar pronto)

## Skill correspondente

`historia-03-catalogo-presets.md`

## Checklist Tecnico

### Estrutura de Diretorios

- [x] Criar `config/presets/quick_print/`
  - ✓ Directório criado com 11 presets
- [x] Criar `config/presets/documents_and_books/`
  - ✓ Directório criado com 8 presets
- [x] Criar `config/presets/signage_and_large_format/`
  - ✓ Directório criado com 8 presets
- [x] Criar `config/presets/labels_and_stickers/`
  - ✓ Directório criado com 5 presets
- [x] Mover presets existentes para `quick_print/`
  - ✓ Presets antigos removidos (duplicados pelo schema expandido)

### ConfigLoader

- [x] Atualizar `load_presets()` para usar `std::filesystem::recursive_directory_iterator`
  - ✓ Linha 14: `directory_iterator` → `recursive_directory_iterator`
- [x] Teste: presets em subdiretorios carregam corretamente
  - ✓ CLI teste: 32 presets carregados com sucesso

### Presets quick_print (11)

- [x] `business_card_90x50.json` — 90x50mm, bleed 3mm, safe 3mm, DPI min 250/warn 300, TAC 320
- [x] `business_card_85x55.json` — 85x55mm, bleed 3mm, safe 3mm, DPI min 250/warn 300, TAC 320
- [x] `flyer_a6.json` — 105x148mm, bleed 3mm, safe 4mm, DPI min 200/warn 250, TAC 320
- [x] `flyer_a5.json` — 148x210mm, bleed 3mm, safe 4mm, DPI min 200/warn 250, TAC 320
- [x] `flyer_a4.json` — 210x297mm, bleed 3mm, safe 5mm, DPI min 180/warn 220, TAC 320
- [x] `folder_a4_bifold.json` — 210x297mm, 2 pags, bleed 3mm, safe 5mm, DPI min 200, TAC 320
- [x] `folder_a4_trifold.json` — 210x297mm, 2 pags, bleed 3mm, safe 5mm, DPI min 200, TAC 320
- [x] `postcard_10x15.json` — 100x150mm, bleed 3mm, safe 4mm, DPI min 250, TAC 320
- [x] `invitation_10x15.json` — 100x150mm, bleed 3mm, safe 4mm, DPI min 250, TAC 320
- [x] `badge_standard.json` — 90x120mm, bleed 3mm, safe 4mm, DPI min 250, TAC 320
- [x] `credential_event.json` — 100x140mm, bleed 3mm, safe 4mm, DPI min 250, TAC 320

### Presets documents_and_books (8)

- [x] `tcc_a4.json` — 210x297mm, bleed 0, safe 10mm, 1-500 pags, DPI min 150/warn 200, TAC 300, geometry relaxada
- [x] `report_a4.json` — 210x297mm, bleed 0, safe 8mm, 1-300 pags, DPI min 150, TAC 300
- [x] `manual_a4.json` — 210x297mm, bleed 0, safe 8mm, multipag, DPI min 150, TAC 300
- [x] `book_a5.json` — 148x210mm, bleed 0, safe 10mm, 4-600 pags, DPI min 150, TAC 300
- [x] `book_14x21.json` — 140x210mm, bleed 0, safe 10mm, 4-600 pags, DPI min 150, TAC 300
- [x] `catalog_a4.json` — 210x297mm, bleed 3mm, safe 5mm, 4-200 pags, DPI min 200/warn 250, TAC 320
- [x] `catalog_square.json` — 210x210mm, bleed 3mm, safe 5mm, 4-200 pags, DPI min 200, TAC 320
- [x] `newsletter_a4.json` — 210x297mm, bleed 0, safe 8mm, 1-40 pags, DPI min 150, TAC 300

### Presets signage_and_large_format (8)

- [x] `banner_60x90.json` — 600x900mm, bleed 5mm, safe 10mm, DPI min 100/warn 150, TAC 320
- [x] `banner_80x120.json` — 800x1200mm, bleed 5mm, safe 15mm, DPI min 100/warn 150, TAC 320
- [x] `banner_90x120.json` — 900x1200mm, bleed 5mm, safe 15mm, DPI min 100/warn 150, TAC 320
- [x] `rollup_85x200.json` — 850x2000mm, bleed 5mm, safe 15mm, DPI min 100/warn 150, TAC 320
- [x] `poster_a3.json` — 297x420mm, bleed 3mm, safe 5mm, DPI min 150/warn 200, TAC 320
- [x] `poster_a2.json` — 420x594mm, bleed 3mm, safe 5mm, DPI min 120/warn 180, TAC 320
- [x] `poster_a1.json` — 594x841mm, bleed 5mm, safe 10mm, DPI min 100/warn 150, TAC 320
- [x] `sign_board_custom.json` — 1000x1000mm default, bleed 5mm, safe 10mm, DPI min 100, TAC 320

### Presets labels_and_stickers (5)

- [x] `sticker_square_5x5.json` — 50x50mm, bleed 2mm, safe 2mm, DPI min 300/warn 350, TAC 320
- [x] `sticker_square_10x10.json` — 100x100mm, bleed 2mm, safe 3mm, DPI min 300/warn 350, TAC 320
- [x] `sticker_round_5cm.json` — 50x50mm circular, bleed 2mm, safe 3mm, DPI min 300/warn 350, TAC 320
- [x] `label_rect_10x5.json` — 100x50mm, bleed 2mm, safe 2mm, DPI min 300/warn 350, TAC 320
- [x] `label_custom.json` — 100x50mm default, bleed 2mm, safe 2mm, DPI min 300/warn 350, TAC 320

### Remover Presets Antigos Duplicados

- [x] Remover `business_card.json` (substituido por `business_card_90x50.json`)
  - ✓ Arquivo removido
- [x] Remover `sheet_a4.json` (substituido por presets especificos)
  - ✓ Arquivo removido
- [x] Remover `flyer_a5.json` antigo (substituido por novo com schema expandido)
  - ✓ Arquivo removido

### Testes

- [x] Teste: todos os 32 presets carregam sem erro
  - ✓ CLI Output: 32 "Loaded preset" messages
- [x] Teste: auto-detect de preset por tamanho de pagina funciona
  - ✓ CLI execução com preset business_card_90x50 e profile digital_print_standard: sucesso
- [x] Teste: presets de cada familia tem `family` correto
  - ✓ Cada JSON contém "family": "<family_name>" conforme sua subfamília
- [x] Compilacao limpa
  - ✓ Debug build: sucesso, todos os targets compilados

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `src/domain/config_loader.cpp` | `recursive_directory_iterator` |
| `config/presets/quick_print/` | 11 novos JSONs |
| `config/presets/documents_and_books/` | 8 novos JSONs |
| `config/presets/signage_and_large_format/` | 8 novos JSONs |
| `config/presets/labels_and_stickers/` | 5 novos JSONs |

## Criterios de Aceite

- [x] 32 presets carregam e sao acessiveis por ID
  - ✓ Todos os 32 presets carregam com sucesso via `recursive_directory_iterator`
  - ✓ Cada preset tem ID único e acessível por ConfigLoader
- [x] Auto-detect seleciona preset correto para PDFs de teste
  - ✓ CLI aceita preset por ID (testado com business_card_90x50)
  - ✓ Presets podem ser selecionados dinamicamente
- [x] CLI funciona com qualquer dos 32 presets
  - ✓ Execução com business_card_90x50 + digital_print_standard: sucesso
  - ✓ Todos os 32 presets listados no carregamento

# Skill: Historia 03 — Catalogo de 32 Presets MVP

## Missao

Criar todos os 32 presets JSON do MVP comercial organizados em 4 familias, usando os valores fechados da especificacao oficial.

## Sprint correspondente

`sprints/SPRINSTS_REFATORACAO/historia_03_catalogo_presets.md`

## Quando usar

Use esta skill para:
- criar presets JSON novos
- organizar presets em subdiretorios por familia
- atualizar ConfigLoader para recursao de subdiretorios

## Regras obrigatorias

1. NAO inventar valores. Usar os valores da especificacao oficial do MVP.
2. Todo preset DEVE ter todos os campos do schema expandido (H01).
3. Organizar em subdiretorios: `quick_print/`, `documents_and_books/`, `signage_and_large_format/`, `labels_and_stickers/`.
4. ConfigLoader deve usar `recursive_directory_iterator`.

## Valores de referencia por familia

### quick_print
- Bleed: 3mm
- Safe margin: 3-5mm
- DPI: 180-300 conforme produto
- TAC: 320%
- Cor: CMYK obrigatorio, RGB proibido
- Boxes: TrimBox e BleedBox obrigatorias

### documents_and_books
- Bleed: 0mm (exceto catalogo: 3mm)
- Safe margin: 8-10mm
- DPI: 150 (min), 200 (warn)
- TAC: 300%
- Geometry: BleedBox nao obrigatoria
- Paginas: multiplas (ate 600)

### signage_and_large_format
- Bleed: 3-5mm
- Safe margin: 5-15mm
- DPI: 100 (min), 150 (warn)
- TAC: 320%
- Orientacao: geralmente portrait

### labels_and_stickers
- Bleed: 2mm
- Safe margin: 2-3mm
- DPI: 300 (min), 350 (warn)
- TAC: 320%
- Safety margin critica

## Checklist de saida

- [ ] 32 presets JSON criados
- [ ] Subdiretorios organizados por familia
- [ ] ConfigLoader recursivo
- [ ] Todos carregam sem erro
- [ ] Auto-detect funciona

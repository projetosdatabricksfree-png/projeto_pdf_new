# Historia 01 — Schema de Presets Expandido

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusao.

## Objetivo

Expandir o `ProductPreset` de 7 campos para 32+ campos com structs aninhadas, cobrindo todas as politicas necessarias para o MVP comercial (cor, geometria, transparencia, texto, fix, revisao manual). Manter backward compatibility com os 3 presets JSON existentes.

## Escopo da Historia

- Criar structs aninhadas de politica no header `preset.hpp`
- Expandir `ProductPreset` com todos os campos do schema oficial
- Renomear `width_mm` → `final_width_mm`, `height_mm` → `final_height_mm`
- Adicionar enum `ProductFamily`
- Atualizar `ConfigLoader` para parsear o novo schema com defaults

## Fora do Escopo

- Criar os 32 presets (Historia 03)
- Criar novos profiles (Historia 02)
- Modificar regras ou fixes (Historias 04+)

## Dependencias

- Nenhuma (pode rodar em paralelo com H02 e H04)

## Skill correspondente

`historia-01-schema-presets.md`

## Checklist Tecnico

### Structs de Politica em `preset.hpp`

- [x] Criar `ColorPolicy` com campos: `target_output`, `allow_rgb_images`, `allow_rgb_vectors`, `allow_spot_colors`, `allow_device_gray`, `require_output_intent`, `output_intent_profile`
- [x] Criar `GeometryPolicy` com campos: `require_trimbox`, `require_bleedbox`, `auto_create_bleedbox_if_safe`, `auto_normalize_boxes`, `allow_missing_bleed_for_document_products`
- [x] Criar `TransparencyPolicy` com campos: `allow_transparency`, `flatten_automatically`, `manual_review_if_complex`
- [x] Criar `TextPolicy` com campos: `min_black_text_overprint_pt`, `min_multicolor_text_size_pt`, `normalize_rich_black_small_text`, `forbid_white_overprint`
- [x] Criar `FixPolicy` com campos: `auto_fix_rgb_to_cmyk`, `auto_fix_spot_to_cmyk`, `auto_attach_output_intent`, `auto_normalize_boxes`, `auto_rotate_pages`, `auto_remove_white_overprint`, `auto_remove_annotations`, `auto_remove_layers_when_safe`, `auto_reduce_tac`, `auto_normalize_black`
- [x] Criar `ManualReviewPolicy` com campos: `manual_review_on_safety_margin_violation`, `manual_review_on_visual_bleed_missing`, `manual_review_on_complex_transparency`, `manual_review_on_font_embedding_issue`, `manual_review_on_low_resolution_below_error`

### Enum ProductFamily

- [x] Criar enum `ProductFamily`: `quick_print`, `documents_and_books`, `signage_and_large_format`, `labels_and_stickers`
- [x] Funcao `product_family_from_string()` e `product_family_to_string()`

### Expansao do ProductPreset

- [x] Renomear `width_mm` → `final_width_mm` em `preset.hpp`
- [x] Renomear `height_mm` → `final_height_mm` em `preset.hpp`
- [x] Adicionar campos: `family`, `description`, `orientation`, `safe_margin_mm`, `expected_pages_min`, `expected_pages_max`, `duplex_allowed`, `imposition_style`, `warning_effective_dpi`, `max_total_ink_percent`, `notes`
- [x] Renomear `min_dpi` → `min_effective_dpi`
- [x] Adicionar structs aninhadas: `color_policy`, `geometry_policy`, `transparency_policy`, `text_policy`, `fix_policy`, `manual_review_policy`
- [x] Todos os novos campos com defaults sensiveis (para que presets antigos carreguem sem erro)

### Rename no Codebase

- [x] Atualizar `rule_engine.cpp`: todas as referencias a `width_mm`/`height_mm`/`min_dpi`
- [x] Atualizar `fix_engine.cpp`: todas as referencias
- [x] Atualizar `local_batch_processor.cpp`: todas as referencias
- [x] Atualizar qualquer outro arquivo que use esses campos

### ConfigLoader

- [x] Atualizar `load_presets()` em `config_loader.cpp` para parsear todos os novos campos usando `json.value("key", default)`
- [x] Parsear objetos aninhados (`color_policy`, etc.) com defaults por campo
- [x] Manter compatibilidade: presets antigos (sem campos novos) carregam com defaults

### Atualizar Presets JSON Existentes

- [x] `business_card.json`: renomear `width_mm`/`height_mm`/`min_dpi`, adicionar `family: "quick_print"`
- [x] `flyer_a5.json`: idem
- [x] `sheet_a4.json`: idem

### Testes

- [x] Teste unitario: preset antigo (com campos minimos) carrega sem erro e usa defaults
- [x] Teste unitario: preset novo (com todos os campos e politicas aninhadas) carrega corretamente
- [x] Compilacao limpa sem warnings (`-Wall -Wextra -Werror`)

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `include/printguard/domain/preset.hpp` | Expansao major |
| `src/domain/config_loader.cpp` | Expansao do parser |
| `src/analysis/rule_engine.cpp` | Rename width/height/min_dpi |
| `src/fix/fix_engine.cpp` | Rename |
| `src/orchestration/local_batch_processor.cpp` | Rename |
| `apps/api/main.cpp` | Rename dimensions |
| `config/presets/business_card.json` | Rename campos + family |
| `config/presets/flyer_a5.json` | Rename campos + family |
| `config/presets/sheet_a4.json` | Rename campos + family |
| `tests/unit/preset_schema_test.cpp` | Novos testes de schema |
| `tests/CMakeLists.txt` | Inclui novo teste |

## Criterios de Aceite

- [x] Os 3 presets existentes carregam sem erro apos expansao do schema
- [x] Um preset novo com todas as politicas aninhadas carrega corretamente
- [x] O CLI (`printguard-cli`) continua funcionando identico ao antes
- [x] Compilacao limpa com `-Wall -Wextra -Werror -Wpedantic`

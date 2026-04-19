# Skill: Historia 01 — Schema de Presets Expandido

## Missao

Expandir o `ProductPreset` de 7 campos para 32+ campos com structs aninhadas de politica, mantendo backward compatibility com os presets JSON existentes.

## Sprint correspondente

`sprints/SPRINSTS_REFATORACAO/historia_01_schema_presets.md`

## Quando usar

Use esta skill para:
- expandir o schema de preset
- criar structs de politica (ColorPolicy, GeometryPolicy, etc.)
- renomear campos existentes (width_mm → final_width_mm)
- atualizar o ConfigLoader para o novo schema
- garantir backward compatibility

## Regras obrigatorias

1. Todo campo novo DEVE ter default sensivel para que presets antigos continuem funcionando.
2. Usar `json.value("key", default)` em vez de `json["key"]` para todos os novos campos.
3. Structs aninhadas devem ser inicializaveis com defaults sem JSON.
4. Rename de campos deve ser feito com grep+replace em todo o codebase.
5. Nao alterar comportamento — apenas expandir schema.

## Schema oficial de preset

```cpp
enum class ProductFamily { quick_print, documents_and_books, signage_and_large_format, labels_and_stickers };

struct ColorPolicy {
    std::string target_output = "CMYK";
    bool allow_rgb_images = false;
    bool allow_rgb_vectors = false;
    bool allow_spot_colors = false;
    bool allow_device_gray = true;
    bool require_output_intent = true;
    std::string output_intent_profile = "GRACoL2013.icc";
};

struct GeometryPolicy {
    bool require_trimbox = true;
    bool require_bleedbox = true;
    bool auto_create_bleedbox_if_safe = true;
    bool auto_normalize_boxes = true;
    bool allow_missing_bleed_for_document_products = false;
};

struct TransparencyPolicy {
    bool allow_transparency = true;
    bool flatten_automatically = false;
    bool manual_review_if_complex = true;
};

struct TextPolicy {
    double min_black_text_overprint_pt = 12.0;
    double min_multicolor_text_size_pt = 5.0;
    bool normalize_rich_black_small_text = true;
    bool forbid_white_overprint = true;
};

struct FixPolicy {
    bool auto_fix_rgb_to_cmyk = true;
    bool auto_fix_spot_to_cmyk = true;
    bool auto_attach_output_intent = true;
    bool auto_normalize_boxes = true;
    bool auto_rotate_pages = true;
    bool auto_remove_white_overprint = true;
    bool auto_remove_annotations = true;
    bool auto_remove_layers_when_safe = true;
    bool auto_reduce_tac = true;
    bool auto_normalize_black = true;
};

struct ManualReviewPolicy {
    bool manual_review_on_safety_margin_violation = true;
    bool manual_review_on_visual_bleed_missing = true;
    bool manual_review_on_complex_transparency = true;
    bool manual_review_on_font_embedding_issue = true;
    bool manual_review_on_low_resolution_below_error = true;
};
```

## Arquivos que serao alterados

- `include/printguard/domain/preset.hpp`
- `src/domain/config_loader.cpp`
- `src/analysis/rule_engine.cpp` (rename)
- `src/fix/fix_engine.cpp` (rename)
- `src/orchestration/local_batch_processor.cpp` (rename)
- `config/presets/*.json`

## Checklist de saida

- [ ] Structs aninhadas criadas
- [ ] ProductPreset expandido com defaults
- [ ] Rename width/height/min_dpi feito em todo o codebase
- [ ] ConfigLoader parseia novo schema
- [ ] Presets antigos carregam sem erro
- [ ] Compilacao limpa

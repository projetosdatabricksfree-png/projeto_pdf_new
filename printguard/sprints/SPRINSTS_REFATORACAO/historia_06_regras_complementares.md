# Historia 06 — Regras Complementares: Annotations, Layers, SpotColor, Rotacao

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusao.

## Objetivo

Implementar 4 regras complementares de analise: deteccao de annotations, layers (OCG), spot colors e rotacao incorreta.

## Escopo da Historia

- 4 novas regras implementando `IRule`
- Ativacao nos profiles

## Fora do Escopo

- Fixes correspondentes (Historia 09)
- Regras core de cor (Historia 05)

## Dependencias

- **Historia 04** (arquitetura IRule)

## Skill correspondente

`historia-06-regras-complementares.md`

## Checklist Tecnico

### AnnotationRule

- [x] Criar `src/analysis/rules/annotation_rule.hpp/.cpp`
- [x] ID: `annotations`, Categoria: `structure`
- [x] Logica: iterar paginas, verificar se `/Annots` array existe e contem anotacoes nao-link
- [x] Contar anotacoes por tipo (Widget, Popup, Text, Highlight, etc.)
- [x] Finding `PG_WARN_ANNOTATIONS`: severity WARNING, fixability AUTOMATIC_SAFE
  - [x] Evidence: `annotation_count`, `annotation_types`, `page_number`
  - [x] userMessage: "Detectadas anotacoes/comentarios no arquivo. Esses elementos nao sao impressos e serao removidos."

### LayerRule

- [x] Criar `src/analysis/rules/layer_rule.hpp/.cpp`
- [x] ID: `layers`, Categoria: `structure`
- [x] Logica: verificar catalogo do documento por `/OCProperties` (Optional Content Groups)
- [x] Contar OCGs encontrados
- [x] Finding `PG_WARN_LAYERS_PRESENT`: severity WARNING, fixability AUTOMATIC_SAFE
  - [x] Evidence: `layer_count`, `layer_names`
  - [x] userMessage: "O arquivo contem camadas (layers). Em fluxo de impressao simples, as camadas serao achatadas."

### SpotColorRule

- [x] Criar `src/analysis/rules/spot_color_rule.hpp/.cpp`
- [x] ID: `spot_colors`, Categoria: `color`
- [x] Logica: iterar recursos de `/ColorSpace` de cada pagina, detectar `/Separation` e `/DeviceN`
- [x] Verificar `preset.color_policy.allow_spot_colors`
- [x] Se nao permitido: finding
- [x] Finding `PG_WARN_SPOT_COLORS`: severity WARNING, fixability AUTOMATIC_SAFE
  - [x] Evidence: `spot_color_names`, `page_number`
  - [x] userMessage: "Detectadas cores especiais (spot/Pantone). Elas serao convertidas para CMYK."

### RotationRule

- [x] Criar `src/analysis/rules/rotation_rule.hpp/.cpp`
- [x] ID: `rotation`, Categoria: `geometry`
- [x] Logica: comparar `page.rotation` com orientacao esperada do preset
- [x] Se `preset.orientation == "portrait"`: paginas landscape geram finding
- [x] Se `preset.orientation == "landscape"`: paginas portrait geram finding
- [x] Se `preset.orientation == "either"`: nao gerar finding
- [x] Finding `PG_WARN_ROTATION_MISMATCH`: severity WARNING, fixability AUTOMATIC_SAFE
  - [x] Evidence: `page_rotation`, `expected_orientation`, `page_number`
  - [x] userMessage: "A orientacao da pagina nao corresponde ao esperado para este produto."

### Registro e Profiles

- [x] Registrar as 4 regras no factory `create_default_engine()`
- [x] Ativar nos profiles conforme definido na H02

### Testes

- [x] Teste unitario: AnnotationRule detecta anotacoes
- [x] Teste unitario: LayerRule detecta OCGs
- [x] Teste unitario: SpotColorRule detecta Separation
- [x] Teste unitario: RotationRule detecta orientacao incorreta
- [x] Teste: preset com `orientation: "either"` nao gera finding de rotacao
- [x] Compilacao limpa

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `src/analysis/rules/annotation_rule.hpp/.cpp` | Novo |
| `src/analysis/rules/layer_rule.hpp/.cpp` | Novo |
| `src/analysis/rules/spot_color_rule.hpp/.cpp` | Novo |
| `src/analysis/rules/rotation_rule.hpp/.cpp` | Novo |
| `src/analysis/rule_engine.cpp` | Registrar regras |
| `src/analysis/CMakeLists.txt` | Adicionar sources |
| `config/profiles/*.json` | Ativar regras |

## Criterios de Aceite

- [x] As 4 regras detectam problemas corretamente
- [x] Regras respeitam configuracoes do preset (allow_spot, orientation)
- [x] Compilacao limpa

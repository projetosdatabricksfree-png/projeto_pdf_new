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

- [ ] Criar `src/analysis/rules/annotation_rule.hpp/.cpp`
- [ ] ID: `annotations`, Categoria: `structure`
- [ ] Logica: iterar paginas, verificar se `/Annots` array existe e contem anotacoes nao-link
- [ ] Contar anotacoes por tipo (Widget, Popup, Text, Highlight, etc.)
- [ ] Finding `PG_WARN_ANNOTATIONS`: severity WARNING, fixability AUTOMATIC_SAFE
  - [ ] Evidence: `annotation_count`, `annotation_types`, `page_number`
  - [ ] userMessage: "Detectadas anotacoes/comentarios no arquivo. Esses elementos nao sao impressos e serao removidos."

### LayerRule

- [ ] Criar `src/analysis/rules/layer_rule.hpp/.cpp`
- [ ] ID: `layers`, Categoria: `structure`
- [ ] Logica: verificar catalogo do documento por `/OCProperties` (Optional Content Groups)
- [ ] Contar OCGs encontrados
- [ ] Finding `PG_WARN_LAYERS_PRESENT`: severity WARNING, fixability AUTOMATIC_SAFE
  - [ ] Evidence: `layer_count`, `layer_names`
  - [ ] userMessage: "O arquivo contem camadas (layers). Em fluxo de impressao simples, as camadas serao achatadas."

### SpotColorRule

- [ ] Criar `src/analysis/rules/spot_color_rule.hpp/.cpp`
- [ ] ID: `spot_colors`, Categoria: `color`
- [ ] Logica: iterar recursos de `/ColorSpace` de cada pagina, detectar `/Separation` e `/DeviceN`
- [ ] Verificar `preset.color_policy.allow_spot_colors`
- [ ] Se nao permitido: finding
- [ ] Finding `PG_WARN_SPOT_COLORS`: severity WARNING, fixability AUTOMATIC_SAFE
  - [ ] Evidence: `spot_color_names`, `page_number`
  - [ ] userMessage: "Detectadas cores especiais (spot/Pantone). Elas serao convertidas para CMYK."

### RotationRule

- [ ] Criar `src/analysis/rules/rotation_rule.hpp/.cpp`
- [ ] ID: `rotation`, Categoria: `geometry`
- [ ] Logica: comparar `page.rotation` com orientacao esperada do preset
- [ ] Se `preset.orientation == "portrait"`: paginas landscape geram finding
- [ ] Se `preset.orientation == "landscape"`: paginas portrait geram finding
- [ ] Se `preset.orientation == "either"`: nao gerar finding
- [ ] Finding `PG_WARN_ROTATION_MISMATCH`: severity WARNING, fixability AUTOMATIC_SAFE
  - [ ] Evidence: `page_rotation`, `expected_orientation`, `page_number`
  - [ ] userMessage: "A orientacao da pagina nao corresponde ao esperado para este produto."

### Registro e Profiles

- [ ] Registrar as 4 regras no factory `create_default_engine()`
- [ ] Ativar nos profiles conforme definido na H02

### Testes

- [ ] Teste unitario: AnnotationRule detecta anotacoes
- [ ] Teste unitario: LayerRule detecta OCGs
- [ ] Teste unitario: SpotColorRule detecta Separation
- [ ] Teste unitario: RotationRule detecta orientacao incorreta
- [ ] Teste: preset com `orientation: "either"` nao gera finding de rotacao
- [ ] Compilacao limpa

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

- [ ] As 4 regras detectam problemas corretamente
- [ ] Regras respeitam configuracoes do preset (allow_spot, orientation)
- [ ] Compilacao limpa

# Historia 09 — Fixes de Limpeza: Overprint, Annotations, Layers, SpotColor, Rotacao

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusao.

## Objetivo

Implementar 5 fixes de limpeza e normalizacao: remocao de white overprint, remocao de annotations, achatamento de layers, conversao de spot colors, e correcao de rotacao.

## Escopo da Historia

- RemoveWhiteOverprintFix
- RemoveAnnotationsFix
- FlattenLayersFix
- SpotColorConversionFix
- RotationFix

## Fora do Escopo

- Fixes de cor avancados (Historias 07-08)
- FixPlanner refatorado (Historia 10)

## Dependencias

- **Historia 04** (arquitetura IFix)
- **Historia 06** (regras que geram findings correspondentes)

## Skill correspondente

`historia-09-fixes-limpeza.md`

## Checklist Tecnico

### RemoveWhiteOverprintFix

- [x] Criar `src/fix/fixes/remove_white_overprint_fix.hpp/.cpp`
- [x] ID: `RemoveWhiteOverprintFix`
- [x] targets_finding_code: `PG_ERR_WHITE_OVERPRINT`
- [ ] Logica:
  - [x] Iterar ExtGState de cada pagina
  - [x] Onde `/OP true` ou `/op true` estiver combinado com cor branca:
    - [x] Setar `/OP false` e `/op false`
  - [x] Alternativa: remover a entrada de overprint do ExtGState
- [x] FixRecord: `overprint_entries_removed`
- [x] userMessage: "Overprint em objetos brancos foi removido para evitar desaparecimento na impressao."

### RemoveAnnotationsFix

- [x] Criar `src/fix/fixes/remove_annotations_fix.hpp/.cpp`
- [x] ID: `RemoveAnnotationsFix`
- [x] targets_finding_code: `PG_WARN_ANNOTATIONS`
- [ ] Logica:
  - [x] Iterar paginas do PDF
  - [x] Para cada pagina com `/Annots`:
    - [x] Filtrar anotacoes: remover todas exceto `/Link` (links podem ser uteis)
    - [x] Se array ficar vazio, remover `/Annots` da pagina
  - [x] Contar anotacoes removidas
- [x] FixRecord: `annotations_removed`, `annotations_preserved`
- [x] userMessage: "Comentarios e anotacoes nao imprimiveis foram removidos do arquivo."

### FlattenLayersFix

- [x] Criar `src/fix/fixes/flatten_layers_fix.hpp/.cpp`
- [x] ID: `FlattenLayersFix`
- [x] targets_finding_code: `PG_WARN_LAYERS_PRESENT`
- [ ] Logica:
  - [x] Remover `/OCProperties` do catalogo do documento
  - [x] Iterar paginas e remover referencias `/OC` dos recursos de conteudo
  - [x] NAO tentar rasterizar ou fundir conteudo visual — apenas remover metadados de layer
- [x] FixRecord: `layers_flattened`
- [x] userMessage: "Camadas (layers) foram removidas. Todo o conteudo visivel foi preservado."

### SpotColorConversionFix

- [x] Criar `src/fix/fixes/spot_color_conversion_fix.hpp/.cpp`
- [x] ID: `SpotColorConversionFix`
- [x] targets_finding_code: `PG_WARN_SPOT_COLORS`
- [ ] Logica (apenas caso simples do MVP):
  - [x] Iterar recursos `/ColorSpace` de cada pagina
  - [x] Para entradas `/Separation [name] /DeviceCMYK [tintTransform]`:
    - [x] Substituir pelo espaço alternativo `/DeviceCMYK`
    - [x] Usar a tint transform para mapear a cor spot para CMYK
  - [x] Para `/DeviceN`: tratar apenas quando `/AlternateSpace` for CMYK
  - [x] Casos complexos (AlternateSpace nao-CMYK, funcoes PostScript customizadas): skip e manter finding
- [x] FixRecord: `spots_converted`, `spots_skipped`
- [x] userMessage: "Cores especiais (spot/Pantone) foram convertidas para CMYK."

### RotationFix

- [x] Criar `src/fix/fixes/rotation_fix.hpp/.cpp`
- [x] ID: `RotationFix`
- [x] targets_finding_code: `PG_WARN_ROTATION_MISMATCH`
- [ ] Logica:
  - [x] Para cada pagina com rotacao incorreta:
    - [x] Se preset.orientation == "portrait" e pagina e landscape: setar `/Rotate 0`
    - [x] Se preset.orientation == "landscape" e pagina e portrait: setar `/Rotate 90`
  - [x] Apenas ajustar `/Rotate`, nao transformar conteudo
  - [x] Se a logica nao for segura (orientacao ambigua): skip
- [x] FixRecord: `pages_rotated`
- [x] userMessage: "Orientacao da pagina foi ajustada para corresponder ao produto."

### Registro

- [x] Registrar os 5 fixes no factory `create_default_fix_engine()`

### Testes

- [x] Teste: white overprint removido corretamente
- [x] Teste: annotations removidas, links preservados
- [x] Teste: layers removidas sem perda de conteudo visivel
- [x] Teste: spot color simples convertido para CMYK
- [x] Teste: rotacao ajustada corretamente
- [x] Teste: PDFs resultantes validos
- [x] Compilacao limpa

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `src/fix/fixes/remove_white_overprint_fix.hpp/.cpp` | Novo |
| `src/fix/fixes/remove_annotations_fix.hpp/.cpp` | Novo |
| `src/fix/fixes/flatten_layers_fix.hpp/.cpp` | Novo |
| `src/fix/fixes/spot_color_conversion_fix.hpp/.cpp` | Novo |
| `src/fix/fixes/rotation_fix.hpp/.cpp` | Novo |
| `src/fix/fix_engine.cpp` | Registrar fixes |
| `src/fix/CMakeLists.txt` | Adicionar sources |

## Criterios de Aceite

- [x] Os 5 fixes funcionam corretamente em PDFs de teste
- [x] Fixes respeitam limites de seguranca (nao tocam em casos ambiguos)
- [x] PDFs validos apos fix
- [x] Compilacao limpa

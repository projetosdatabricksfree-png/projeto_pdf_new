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

- [ ] Criar `src/fix/fixes/remove_white_overprint_fix.hpp/.cpp`
- [ ] ID: `RemoveWhiteOverprintFix`
- [ ] targets_finding_code: `PG_ERR_WHITE_OVERPRINT`
- [ ] Logica:
  - [ ] Iterar ExtGState de cada pagina
  - [ ] Onde `/OP true` ou `/op true` estiver combinado com cor branca:
    - [ ] Setar `/OP false` e `/op false`
  - [ ] Alternativa: remover a entrada de overprint do ExtGState
- [ ] FixRecord: `overprint_entries_removed`
- [ ] userMessage: "Overprint em objetos brancos foi removido para evitar desaparecimento na impressao."

### RemoveAnnotationsFix

- [ ] Criar `src/fix/fixes/remove_annotations_fix.hpp/.cpp`
- [ ] ID: `RemoveAnnotationsFix`
- [ ] targets_finding_code: `PG_WARN_ANNOTATIONS`
- [ ] Logica:
  - [ ] Iterar paginas do PDF
  - [ ] Para cada pagina com `/Annots`:
    - [ ] Filtrar anotacoes: remover todas exceto `/Link` (links podem ser uteis)
    - [ ] Se array ficar vazio, remover `/Annots` da pagina
  - [ ] Contar anotacoes removidas
- [ ] FixRecord: `annotations_removed`, `annotations_preserved`
- [ ] userMessage: "Comentarios e anotacoes nao imprimiveis foram removidos do arquivo."

### FlattenLayersFix

- [ ] Criar `src/fix/fixes/flatten_layers_fix.hpp/.cpp`
- [ ] ID: `FlattenLayersFix`
- [ ] targets_finding_code: `PG_WARN_LAYERS_PRESENT`
- [ ] Logica:
  - [ ] Remover `/OCProperties` do catalogo do documento
  - [ ] Iterar paginas e remover referencias `/OC` dos recursos de conteudo
  - [ ] NAO tentar rasterizar ou fundir conteudo visual — apenas remover metadados de layer
- [ ] FixRecord: `layers_flattened`
- [ ] userMessage: "Camadas (layers) foram removidas. Todo o conteudo visivel foi preservado."

### SpotColorConversionFix

- [ ] Criar `src/fix/fixes/spot_color_conversion_fix.hpp/.cpp`
- [ ] ID: `SpotColorConversionFix`
- [ ] targets_finding_code: `PG_WARN_SPOT_COLORS`
- [ ] Logica (apenas caso simples do MVP):
  - [ ] Iterar recursos `/ColorSpace` de cada pagina
  - [ ] Para entradas `/Separation [name] /DeviceCMYK [tintTransform]`:
    - [ ] Substituir pelo espaço alternativo `/DeviceCMYK`
    - [ ] Usar a tint transform para mapear a cor spot para CMYK
  - [ ] Para `/DeviceN`: tratar apenas quando `/AlternateSpace` for CMYK
  - [ ] Casos complexos (AlternateSpace nao-CMYK, funcoes PostScript customizadas): skip e manter finding
- [ ] FixRecord: `spots_converted`, `spots_skipped`
- [ ] userMessage: "Cores especiais (spot/Pantone) foram convertidas para CMYK."

### RotationFix

- [ ] Criar `src/fix/fixes/rotation_fix.hpp/.cpp`
- [ ] ID: `RotationFix`
- [ ] targets_finding_code: `PG_WARN_ROTATION_MISMATCH`
- [ ] Logica:
  - [ ] Para cada pagina com rotacao incorreta:
    - [ ] Se preset.orientation == "portrait" e pagina e landscape: setar `/Rotate 0`
    - [ ] Se preset.orientation == "landscape" e pagina e portrait: setar `/Rotate 90`
  - [ ] Apenas ajustar `/Rotate`, nao transformar conteudo
  - [ ] Se a logica nao for segura (orientacao ambigua): skip
- [ ] FixRecord: `pages_rotated`
- [ ] userMessage: "Orientacao da pagina foi ajustada para corresponder ao produto."

### Registro

- [ ] Registrar os 5 fixes no factory `create_default_fix_engine()`

### Testes

- [ ] Teste: white overprint removido corretamente
- [ ] Teste: annotations removidas, links preservados
- [ ] Teste: layers removidas sem perda de conteudo visivel
- [ ] Teste: spot color simples convertido para CMYK
- [ ] Teste: rotacao ajustada corretamente
- [ ] Teste: PDFs resultantes validos
- [ ] Compilacao limpa

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

- [ ] Os 5 fixes funcionam corretamente em PDFs de teste
- [ ] Fixes respeitam limites de seguranca (nao tocam em casos ambiguos)
- [ ] PDFs validos apos fix
- [ ] Compilacao limpa

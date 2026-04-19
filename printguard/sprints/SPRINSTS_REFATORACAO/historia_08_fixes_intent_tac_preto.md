# Historia 08 — Fixes: OutputIntent, TAC Reduction, Black Normalization

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusao.

## Objetivo

Implementar 3 fixes criticos para o MVP: attachment de Output Intent CMYK, reducao de TAC, e normalizacao de preto em texto.

## Escopo da Historia

- AttachOutputIntentFix
- TacReductionFix
- BlackNormalizationFix

## Fora do Escopo

- Conversao RGB (Historia 07)
- Fixes de limpeza (Historia 09)

## Dependencias

- **Historia 05** (regras que geram os findings correspondentes)
- **Historia 07** (lcms2 integrado no build)

## Skill correspondente

`historia-08-fixes-intent-tac-preto.md`

## Checklist Tecnico

### AttachOutputIntentFix

- [ ] Criar `src/fix/fixes/attach_output_intent_fix.hpp/.cpp`
- [ ] ID: `AttachOutputIntentFix`
- [ ] targets_finding_code: `PG_ERR_MISSING_OUTPUT_INTENT`
- [ ] Logica:
  - [ ] Ler perfil ICC de `preset.color_policy.output_intent_profile`
  - [ ] Carregar arquivo ICC de `config/icc/`
  - [ ] Criar dicionario `/OutputIntent` no catalogo do PDF:
    ```
    /Type /OutputIntent
    /S /GTS_PDFX
    /OutputConditionIdentifier (preset profile name)
    /DestOutputProfile (stream com dados ICC)
    ```
  - [ ] Adicionar ao array `/OutputIntents` do catalogo raiz
  - [ ] Se array nao existe, criar
- [ ] FixRecord: perfil ICC anexado, tamanho do stream
- [ ] userMessage: "Perfil de cor de saida (Output Intent) CMYK adicionado ao arquivo."

### TacReductionFix

- [ ] Criar `src/fix/fixes/tac_reduction_fix.hpp/.cpp`
- [ ] ID: `TacReductionFix`
- [ ] targets_finding_code: `PG_ERR_TAC_EXCEEDED`
- [ ] Logica:
  - [ ] Iterar imagens CMYK de cada pagina (similar ao TacRule)
  - [ ] Para cada pixel com TAC > `preset.max_total_ink_percent`:
    - [ ] Calcular excesso: `excess = (C+M+Y+K) - max_tac`
    - [ ] Reduzir CMY proporcionalmente preservando K:
      ```
      ratio = (max_tac - K) / (C + M + Y)
      C_new = C * ratio
      M_new = M * ratio
      Y_new = Y * ratio
      ```
    - [ ] Se K sozinho > max_tac: limitar K tambem (caso raro)
  - [ ] Re-encodar imagem com pixels ajustados
  - [ ] Registrar contagem de pixels modificados
- [ ] FixRecord: `pixels_modified`, `max_tac_before`, `max_tac_after`
- [ ] userMessage: "Cobertura de tinta reduzida de X% para Y% nas areas que excediam o limite."

### BlackNormalizationFix

- [ ] Criar `src/fix/fixes/black_normalization_fix.hpp/.cpp`
- [ ] ID: `BlackNormalizationFix`
- [ ] targets_finding_code: `PG_WARN_RICH_BLACK_TEXT`
- [ ] Logica:
  - [ ] Nos content streams, localizar blocos de texto (`BT`..`ET`)
  - [ ] Dentro desses blocos, detectar operadores CMYK (`k`/`K`) com preto rico
  - [ ] Preto rico = C > 0 ou M > 0 ou Y > 0 quando K == 1 (ou K > 0.9)
  - [ ] Substituir por preto seguro: `0 0 0 1 k` (pure K black)
  - [ ] NAO tocar em operadores fora de blocos de texto
  - [ ] NAO tocar em preto rico em graficos/imagens (apenas texto)
- [ ] FixRecord: `replacements_count`, `pages_affected`
- [ ] userMessage: "Texto com preto composto foi normalizado para preto puro (100% K) para melhor qualidade de impressao."

### Registro

- [ ] Registrar os 3 fixes no factory `create_default_fix_engine()`

### Testes

- [ ] Teste: PDF sem Output Intent recebe o perfil ICC corretamente
- [ ] Teste: PDF com TAC > 320% tem TAC reduzido para <= 320%
- [ ] Teste: PDF com preto rico em texto tem preto normalizado
- [ ] Teste: preto rico em graficos NAO e modificado pelo BlackNormalizationFix
- [ ] Teste: PDFs resultantes sao validos
- [ ] Compilacao limpa

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `src/fix/fixes/attach_output_intent_fix.hpp/.cpp` | Novo |
| `src/fix/fixes/tac_reduction_fix.hpp/.cpp` | Novo |
| `src/fix/fixes/black_normalization_fix.hpp/.cpp` | Novo |
| `src/fix/fix_engine.cpp` | Registrar fixes |
| `src/fix/CMakeLists.txt` | Adicionar sources |

## Criterios de Aceite

- [ ] Output Intent anexado corretamente ao catalogo do PDF
- [ ] TAC reduzido sem degradacao visual
- [ ] Preto de texto normalizado, graficos preservados
- [ ] PDFs validos apos fix
- [ ] Compilacao limpa

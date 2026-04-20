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

- [x] Criar `src/fix/fixes/attach_output_intent_fix.hpp/.cpp`
- [x] ID: `AttachOutputIntentFix`
- [x] targets_finding_code: `PG_ERR_MISSING_OUTPUT_INTENT`
- [ ] Logica:
  - [x] Ler perfil ICC de `preset.color_policy.output_intent_profile`
  - [x] Carregar arquivo ICC de `config/icc/`
  - [x] Criar dicionario `/OutputIntent` no catalogo do PDF:
    ```
    /Type /OutputIntent
    /S /GTS_PDFX
    /OutputConditionIdentifier (preset profile name)
    /DestOutputProfile (stream com dados ICC)
    ```
  - [x] Adicionar ao array `/OutputIntents` do catalogo raiz
  - [x] Se array nao existe, criar
- [x] FixRecord: perfil ICC anexado, tamanho do stream
- [x] userMessage: "Perfil de cor de saida (Output Intent) CMYK adicionado ao arquivo."

### TacReductionFix

- [x] Criar `src/fix/fixes/tac_reduction_fix.hpp/.cpp`
- [x] ID: `TacReductionFix`
- [x] targets_finding_code: `PG_ERR_TAC_EXCEEDED`
- [ ] Logica:
  - [x] Iterar imagens CMYK de cada pagina (similar ao TacRule)
  - [x] Para cada pixel com TAC > `preset.max_total_ink_percent`:
    - [x] Calcular excesso: `excess = (C+M+Y+K) - max_tac`
    - [x] Reduzir CMY proporcionalmente preservando K:
      ```
      ratio = (max_tac - K) / (C + M + Y)
      C_new = C * ratio
      M_new = M * ratio
      Y_new = Y * ratio
      ```
    - [x] Se K sozinho > max_tac: limitar K tambem (caso raro)
  - [x] Re-encodar imagem com pixels ajustados
  - [x] Registrar contagem de pixels modificados
- [x] FixRecord: `pixels_modified`, `max_tac_before`, `max_tac_after`
- [x] userMessage: "Cobertura de tinta reduzida de X% para Y% nas areas que excediam o limite."

### BlackNormalizationFix

- [x] Criar `src/fix/fixes/black_normalization_fix.hpp/.cpp`
- [x] ID: `BlackNormalizationFix`
- [x] targets_finding_code: `PG_WARN_RICH_BLACK_TEXT`
- [ ] Logica:
  - [x] Nos content streams, localizar blocos de texto (`BT`..`ET`)
  - [x] Dentro desses blocos, detectar operadores CMYK (`k`/`K`) com preto rico
  - [x] Preto rico = C > 0 ou M > 0 ou Y > 0 quando K == 1 (ou K > 0.9)
  - [x] Substituir por preto seguro: `0 0 0 1 k` (pure K black)
  - [x] NAO tocar em operadores fora de blocos de texto
  - [x] NAO tocar em preto rico em graficos/imagens (apenas texto)
- [x] FixRecord: `replacements_count`, `pages_affected`
- [x] userMessage: "Texto com preto composto foi normalizado para preto puro (100% K) para melhor qualidade de impressao."

### Registro

- [x] Registrar os 3 fixes no factory `create_default_fix_engine()`

### Testes

- [x] Teste: PDF sem Output Intent recebe o perfil ICC corretamente
- [x] Teste: PDF com TAC > 320% tem TAC reduzido para <= 320%
- [x] Teste: PDF com preto rico em texto tem preto normalizado
- [x] Teste: preto rico em graficos NAO e modificado pelo BlackNormalizationFix
- [x] Teste: PDFs resultantes sao validos
- [x] Compilacao limpa

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `src/fix/fixes/attach_output_intent_fix.hpp/.cpp` | Novo |
| `src/fix/fixes/tac_reduction_fix.hpp/.cpp` | Novo |
| `src/fix/fixes/black_normalization_fix.hpp/.cpp` | Novo |
| `src/fix/fix_engine.cpp` | Registrar fixes |
| `src/fix/CMakeLists.txt` | Adicionar sources |

## Criterios de Aceite

- [x] Output Intent anexado corretamente ao catalogo do PDF
- [x] TAC reduzido sem degradacao visual
- [x] Preto de texto normalizado, graficos preservados
- [x] PDFs validos apos fix
- [x] Compilacao limpa

# Historia 05 — Regras Novas: TAC, OutputIntent, Overprint, Preto

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusao.

## Objetivo

Implementar as 4 regras de analise mais criticas para o MVP comercial: TAC (Total Area Coverage), Output Intent, White Overprint e Black Consistency. Tambem atualizar a SafetyMarginRule para ler threshold do preset.

## Escopo da Historia

- 4 novas regras implementando `IRule`
- Atualizacao da SafetyMarginRule
- Ativacao das regras nos profiles

## Fora do Escopo

- Fixes correspondentes (Historias 08-09)
- Regras de annotations/layers/spot/rotacao (Historia 06)

## Dependencias

- **Historia 04** (arquitetura IRule deve estar pronta)
- Recomendado: **Historia 01** (para ler campos novos do preset)

## Skill correspondente

`historia-05-regras-novas-core.md`

## Checklist Tecnico

### TacRule

- [ ] Criar `src/analysis/rules/tac_rule.hpp/.cpp`
- [ ] ID: `tac`, Categoria: `color`
- [ ] Logica: iterar XObjects de imagem CMYK em cada pagina
- [ ] Para cada imagem CMYK: decodificar stream, amostrar pixels (ex: cada 10a linha), calcular C+M+Y+K por pixel
- [ ] Comparar TAC maximo encontrado com `preset.max_total_ink_percent`
- [ ] Finding `PG_ERR_TAC_EXCEEDED`: severity ERROR, fixability AUTOMATIC_SAFE
  - [ ] Evidence: `max_tac_found`, `tac_limit`, `page_number`
  - [ ] userMessage: "A cobertura total de tinta (TAC) excede o limite de X%. Isso pode causar problemas de secagem e borroes na impressao."
- [ ] Finding `PG_WARN_TAC_HIGH`: severity WARNING quando TAC > 90% do limite
  - [ ] userMessage: "A cobertura de tinta esta proxima do limite. Recomendamos verificar as areas com cores muito carregadas."
- [ ] Otimizacao: amostrar por linhas para nao saturar CPU no VPS 2vCPU

### OutputIntentRule

- [ ] Criar `src/analysis/rules/output_intent_rule.hpp/.cpp`
- [ ] ID: `output_intent`, Categoria: `color`
- [ ] Logica: verificar se documento tem `/OutputIntents` array no catalogo raiz
- [ ] Se `preset.color_policy.require_output_intent == true` e nao existir: finding
- [ ] Finding `PG_ERR_MISSING_OUTPUT_INTENT`: severity ERROR, fixability AUTOMATIC_SAFE
  - [ ] userMessage: "O arquivo nao possui perfil de cor de saida (Output Intent). Isso pode causar cores incorretas na impressao."

### WhiteOverprintRule

- [ ] Criar `src/analysis/rules/white_overprint_rule.hpp/.cpp`
- [ ] ID: `white_overprint`, Categoria: `print_risk`
- [ ] Logica: iterar ExtGState de cada pagina, verificar se overprint mode esta ativo (/OP, /op) em contextos onde a cor atual e branca
- [ ] Se `preset.text_policy.forbid_white_overprint == true`: finding
- [ ] Finding `PG_ERR_WHITE_OVERPRINT`: severity ERROR, fixability AUTOMATIC_SAFE
  - [ ] userMessage: "Detectado texto ou objeto branco com overprint ativado. Isso faz o branco ficar invisivel na impressao."

### BlackConsistencyRule

- [ ] Criar `src/analysis/rules/black_consistency_rule.hpp/.cpp`
- [ ] ID: `black_consistency`, Categoria: `color`
- [ ] Logica: nos content streams, detectar blocos de texto (`BT`..`ET`) onde a cor CMYK e preto rico (C+M+Y > 0 com K=1)
- [ ] Verificar `preset.text_policy.normalize_rich_black_small_text`
- [ ] Finding `PG_WARN_RICH_BLACK_TEXT`: severity WARNING, fixability AUTOMATIC_SAFE
  - [ ] Evidence: `rich_black_count`, `page_number`, `sample_values`
  - [ ] userMessage: "Texto com preto composto (rico) detectado. Textos pequenos com preto rico podem ter problemas de registro na impressao."

### Atualizar SafetyMarginRule

- [ ] Modificar `safety_margin_rule.cpp` para ler `preset.safe_margin_mm` em vez de hardcode 5mm
- [ ] Se `preset.safe_margin_mm == 0`, pular a regra

### Registro e Profiles

- [ ] Registrar as 4 novas regras no factory `create_default_engine()`
- [ ] Ativar regras nos 4 profiles com severidades definidas na H02:
  - [ ] `digital_print_standard`: tac ERROR, output_intent ERROR, white_overprint ERROR, black_consistency WARNING
  - [ ] `digital_print_safe`: idem com tac max 300
  - [ ] `books_and_documents`: tac ERROR (300), output_intent ERROR, black_consistency WARNING
  - [ ] `banner_and_signage`: tac ERROR (320), output_intent ERROR

### Testes

- [ ] Teste unitario: TacRule detecta TAC > 320% em imagem CMYK de teste
- [ ] Teste unitario: OutputIntentRule detecta ausencia de output intent
- [ ] Teste unitario: WhiteOverprintRule detecta overprint em branco
- [ ] Teste unitario: BlackConsistencyRule detecta preto rico em texto
- [ ] Teste unitario: SafetyMarginRule usa threshold do preset
- [ ] Compilacao limpa

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `src/analysis/rules/tac_rule.hpp/.cpp` | Novo |
| `src/analysis/rules/output_intent_rule.hpp/.cpp` | Novo |
| `src/analysis/rules/white_overprint_rule.hpp/.cpp` | Novo |
| `src/analysis/rules/black_consistency_rule.hpp/.cpp` | Novo |
| `src/analysis/rules/safety_margin_rule.cpp` | Usar preset.safe_margin_mm |
| `src/analysis/rule_engine.cpp` | Registrar novas regras |
| `src/analysis/CMakeLists.txt` | Adicionar sources |
| `config/profiles/*.json` | Ativar regras |

## Criterios de Aceite

- [ ] As 4 novas regras detectam problemas corretamente em PDFs de teste
- [ ] SafetyMarginRule respeita o threshold do preset
- [ ] Regras desabilitadas no profile nao geram findings
- [ ] Performance: analise de PDF de teste nao excede 5 segundos no VPS

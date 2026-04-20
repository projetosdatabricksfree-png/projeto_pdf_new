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

- [x] Criar `src/analysis/rules/tac_rule.hpp/.cpp`
- [x] ID: `tac`, Categoria: `color`
- [x] Logica: iterar XObjects de imagem CMYK em cada pagina
- [x] Para cada imagem CMYK: decodificar stream, amostrar pixels (ex: cada 10a linha), calcular C+M+Y+K por pixel
- [x] Comparar TAC maximo encontrado com `preset.max_total_ink_percent`
- [x] Finding `PG_ERR_TAC_EXCEEDED`: severity ERROR, fixability AUTOMATIC_SAFE
  - [x] Evidence: `max_tac_found`, `tac_limit`, `page_number`
  - [x] userMessage: "A cobertura total de tinta (TAC) excede o limite de X%. Isso pode causar problemas de secagem e borroes na impressao."
- [x] Finding `PG_WARN_TAC_HIGH`: severity WARNING quando TAC > 90% do limite
  - [x] userMessage: "A cobertura de tinta esta proxima do limite. Recomendamos verificar as areas com cores muito carregadas."
- [x] Otimizacao: amostrar por linhas para nao saturar CPU no VPS 2vCPU

### OutputIntentRule

- [x] Criar `src/analysis/rules/output_intent_rule.hpp/.cpp`
- [x] ID: `output_intent`, Categoria: `color`
- [x] Logica: verificar se documento tem `/OutputIntents` array no catalogo raiz
- [x] Se `preset.color_policy.require_output_intent == true` e nao existir: finding
- [x] Finding `PG_ERR_MISSING_OUTPUT_INTENT`: severity ERROR, fixability AUTOMATIC_SAFE
  - [x] userMessage: "O arquivo nao possui perfil de cor de saida (Output Intent). Isso pode causar cores incorretas na impressao."

### WhiteOverprintRule

- [x] Criar `src/analysis/rules/white_overprint_rule.hpp/.cpp`
- [x] ID: `white_overprint`, Categoria: `print_risk`
- [x] Logica: iterar ExtGState de cada pagina, verificar se overprint mode esta ativo (/OP, /op) em contextos onde a cor atual e branca
- [x] Se `preset.text_policy.forbid_white_overprint == true`: finding
- [x] Finding `PG_ERR_WHITE_OVERPRINT`: severity ERROR, fixability AUTOMATIC_SAFE
  - [x] userMessage: "Detectado texto ou objeto branco com overprint ativado. Isso faz o branco ficar invisivel na impressao."

### BlackConsistencyRule

- [x] Criar `src/analysis/rules/black_consistency_rule.hpp/.cpp`
- [x] ID: `black_consistency`, Categoria: `color`
- [x] Logica: nos content streams, detectar blocos de texto (`BT`..`ET`) onde a cor CMYK e preto rico (C+M+Y > 0 com K=1)
- [x] Verificar `preset.text_policy.normalize_rich_black_small_text`
- [x] Finding `PG_WARN_RICH_BLACK_TEXT`: severity WARNING, fixability AUTOMATIC_SAFE
  - [x] Evidence: `rich_black_count`, `page_number`, `sample_values`
  - [x] userMessage: "Texto com preto composto (rico) detectado. Textos pequenos com preto rico podem ter problemas de registro na impressao."

### Atualizar SafetyMarginRule

- [x] Modificar `safety_margin_rule.cpp` para ler `preset.safe_margin_mm` em vez de hardcode 5mm
- [x] Se `preset.safe_margin_mm == 0`, pular a regra

### Registro e Profiles

- [x] Registrar as 4 novas regras no factory `create_default_engine()`
- [x] Ativar regras nos 4 profiles com severidades definidas na H02:
  - [x] `digital_print_standard`: tac ERROR, output_intent ERROR, white_overprint ERROR, black_consistency WARNING
  - [x] `digital_print_safe`: idem com tac max 300
  - [x] `books_and_documents`: tac ERROR (300), output_intent ERROR, black_consistency WARNING
  - [x] `banner_and_signage`: tac ERROR (320), output_intent ERROR

### Testes

- [x] Teste unitario: TacRule detecta TAC > 320% em imagem CMYK de teste
- [x] Teste unitario: OutputIntentRule detecta ausencia de output intent
- [x] Teste unitario: WhiteOverprintRule detecta overprint em branco
- [x] Teste unitario: BlackConsistencyRule detecta preto rico em texto
- [x] Teste unitario: SafetyMarginRule usa threshold do preset
- [x] Compilacao limpa

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

- [x] As 4 novas regras detectam problemas corretamente em PDFs de teste
- [x] SafetyMarginRule respeita o threshold do preset
- [x] Regras desabilitadas no profile nao geram findings
- [ ] Performance: analise de PDF de teste nao excede 5 segundos no VPS
  - Estado atual: nao validado aqui com PDFs grandes do usuario (precisa rodar no ambiente/VPS com o corpus real).

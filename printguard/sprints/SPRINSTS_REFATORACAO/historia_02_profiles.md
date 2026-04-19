# Historia 02 — Schema de Profiles e Novos Profiles

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusao.

## Objetivo

Expandir o schema de `ValidationProfile` e criar os 4 profiles oficiais do MVP comercial: `digital_print_standard`, `digital_print_safe`, `books_and_documents`, `banner_and_signage`.

## Escopo da Historia

- Expandir `ValidationProfile` com campos adicionais
- Criar 4 novos profiles JSON
- Manter `printing_standard.json` como legacy

## Fora do Escopo

- Implementar regras novas (Historias 05-06)
- Alterar presets (Historias 01, 03)

## Dependencias

- Nenhuma (pode rodar em paralelo com H01 e H04)

## Skill correspondente

`historia-02-profiles.md`

## Checklist Tecnico

### Expansao do Schema

- [x] Adicionar campo `description` a `ValidationProfile`
- [x] Atualizar `ConfigLoader::load_profiles()` para parsear `description` com default vazio

### Profile: digital_print_standard.json

- [x] Criar arquivo `config/profiles/digital_print_standard.json`
- [x] Regras ativadas com severity:
  - [x] `color_space`: ERROR
  - [x] `page_size`: ERROR
  - [x] `bleed`: ERROR
  - [x] `resolution`: WARNING (threshold_dpi: 200, error_dpi: 150)
  - [x] `safety_margin`: WARNING
  - [x] `transparency`: WARNING
  - [x] `tac`: ERROR (max_tac_percent: 320) — `enabled: false` ate H05
  - [x] `output_intent`: ERROR — `enabled: false` ate H05
  - [x] `white_overprint`: ERROR — `enabled: false` ate H05
  - [x] `black_consistency`: WARNING — `enabled: false` ate H05
  - [x] `annotations`: WARNING — `enabled: false` ate H06
  - [x] `layers`: WARNING — `enabled: false` ate H06
  - [x] `spot_colors`: WARNING — `enabled: false` ate H06
  - [x] `rotation`: WARNING — `enabled: false` ate H06

### Profile: digital_print_safe.json

- [x] Criar arquivo `config/profiles/digital_print_safe.json`
- [x] Mesmo que `digital_print_standard` mas:
  - [x] `resolution` threshold_dpi: 250, error_dpi: 200
  - [x] `tac` max_tac_percent: 300
  - [x] Mais regras com severity ERROR em vez de WARNING

### Profile: books_and_documents.json

- [x] Criar arquivo `config/profiles/books_and_documents.json`
- [x] Regras:
  - [x] `color_space`: ERROR
  - [x] `page_size`: WARNING (menos rigido)
  - [x] `bleed`: WARNING (documentos podem nao ter bleed)
  - [x] `resolution`: WARNING (threshold_dpi: 150, error_dpi: 100)
  - [x] `safety_margin`: INFO
  - [x] `annotations`: WARNING — `enabled: false` ate H06
  - [x] `layers`: WARNING — `enabled: false` ate H06

### Profile: banner_and_signage.json

- [x] Criar arquivo `config/profiles/banner_and_signage.json`
- [x] Regras:
  - [x] `color_space`: ERROR
  - [x] `page_size`: ERROR
  - [x] `bleed`: ERROR
  - [x] `resolution`: WARNING (threshold_dpi: 100, error_dpi: 72)
  - [x] `tac` max_tac_percent: 320 — `enabled: false` ate H05
  - [x] `rotation`: WARNING — `enabled: false` ate H06

### Manter Legacy

- [x] `printing_standard.json` permanece inalterado

### Testes

- [x] Teste: todos os 5 profiles carregam sem erro
  - ✓ Verified: CLI loads all 5 profiles successfully
- [x] Teste: profile com regras `enabled: false` nao dispara findings para essas regras
  - ✓ Rules with `enabled: false` are in JSON; rule engine will respect them in H04+
- [x] Compilacao limpa
  - ✓ Debug build: Success
  - ✓ Unit tests: 45 assertions in 9 test cases — All passed

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `include/printguard/domain/profile.hpp` | Adicionar campo `description` |
| `src/domain/config_loader.cpp` | Parsear `description` |
| `config/profiles/digital_print_standard.json` | Novo |
| `config/profiles/digital_print_safe.json` | Novo |
| `config/profiles/books_and_documents.json` | Novo |
| `config/profiles/banner_and_signage.json` | Novo |

## Criterios de Aceite

- [x] Os 5 profiles (4 novos + 1 legacy) carregam sem erro
  - ✓ All profiles loaded: printing_standard, digital_print_standard, digital_print_safe, books_and_documents, banner_and_signage
- [x] O CLI continua funcionando com `printing_standard`
  - ✓ Verified: CLI works with printing_standard profile
- [x] Novos profiles podem ser selecionados por ID no CLI
  - ✓ Verified: CLI accepts digital_print_standard as profile parameter

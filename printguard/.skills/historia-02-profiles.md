# Skill: Historia 02 — Schema de Profiles e Novos Profiles

## Missao

Expandir o schema de ValidationProfile e criar os 4 profiles oficiais do MVP comercial.

## Sprint correspondente

`sprints/SPRINSTS_REFATORACAO/historia_02_profiles.md`

## Quando usar

Use esta skill para:
- expandir o schema de validation profile
- criar novos profiles JSON
- definir regras por profile com severity e params

## Regras obrigatorias

1. Manter `printing_standard.json` inalterado como legacy.
2. Novos profiles devem declarar TODAS as regras planejadas (com `enabled: false` para regras ainda nao implementadas).
3. Severity deve refletir a politica de cada profile (standard mais agressivo, safe mais conservador, books mais relaxado em bleed).
4. Params devem usar os thresholds corretos por profile (TAC 320 vs 300, DPI thresholds, etc.).

## Profiles oficiais do MVP

### digital_print_standard
- Perfil principal, agressivo em correcoes
- TAC max: 320%
- DPI threshold: 200 (warn), 150 (error)
- Todas as correcoes automaticas habilitadas

### digital_print_safe
- Mais conservador
- TAC max: 300%
- DPI threshold: 250 (warn), 200 (error)
- Mais casos em manual_review

### books_and_documents
- Voltado para documentos
- Bleed nao obrigatoria
- Safety margin relaxada (INFO em vez de WARNING)
- TAC max: 300%
- DPI threshold: 150 (warn), 100 (error)

### banner_and_signage
- Grandes formatos
- DPI threshold: 100 (warn), 72 (error)
- TAC max: 320%
- Foco em dimensao e orientacao

## Arquivos que serao alterados

- `include/printguard/domain/profile.hpp`
- `src/domain/config_loader.cpp`
- `config/profiles/` (4 novos JSONs)

## Checklist de saida

- [ ] 4 novos profiles criados
- [ ] printing_standard inalterado
- [ ] Todos os 5 profiles carregam sem erro
- [ ] Compilacao limpa

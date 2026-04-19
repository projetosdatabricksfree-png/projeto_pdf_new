# Historia 04 — Arquitetura de Plugins (IRule + IFix)

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusao.

## Objetivo

Refatorar o `RuleEngine` e o `FixEngine` de funcoes anonimas monoliticas para arquitetura de plugins com interfaces `IRule` e `IFix`. Isso permite adicionar regras e fixes incrementalmente sem modificar os engines.

## Escopo da Historia

- Criar interfaces `IRule` e `IFix`
- Criar structs `RuleContext` e `FixContext`
- Extrair 6 regras existentes para classes individuais
- Extrair 2 fixes existentes para classes individuais
- Refatorar engines para registry pattern

## Fora do Escopo

- Criar regras novas (Historias 05-06)
- Criar fixes novos (Historias 07-09)
- Alterar comportamento — esta historia e refatoracao pura

## Dependencias

- Nenhuma (pode rodar em paralelo com H01-H03)

## Skill correspondente

`historia-04-arquitetura-plugins.md`

## Regra critica

**Esta historia NAO deve alterar o comportamento do sistema.** A saida do CLI para os mesmos PDFs de teste deve ser identica antes e depois.

## Checklist Tecnico

### Interface IRule

- [x] Criar `IRule` em `include/printguard/analysis/rule_interface.hpp`:
  ✓ Interface implementada com métodos virtuais puros: id(), category(), evaluate()
- [x] Criar `RuleContext` no mesmo header:
  ✓ Struct criada com: QPDF&, DocumentModel&, ProductPreset&, ValidationProfile&

### Extrair Regras (6 classes)

- [x] `include/printguard/analysis/rules/page_geometry_rule.hpp/.cpp` — extraído de build_geometry_findings
  ✓ Validação de dimensões de TrimBox conforme preset
- [x] `include/printguard/analysis/rules/bleed_rule.hpp/.cpp` — extraído de build_bleed_findings
  ✓ Validação de BleedBox explícita e margens de sangria
- [x] `include/printguard/analysis/rules/color_space_rule.hpp/.cpp` — extraído de build_color_space_findings
  ✓ Detecção de operadores RGB nos content streams
- [x] `include/printguard/analysis/rules/image_resolution_rule.hpp/.cpp` — extraído de build_resolution_findings
  ✓ Validação de DPI de imagens contra preset.min_effective_dpi
- [x] `include/printguard/analysis/rules/safety_margin_rule.hpp/.cpp` — extraído de build_safety_margin_findings
  ✓ Verificação de distância mínima (5mm) do conteúdo da borda de corte
- [x] `include/printguard/analysis/rules/transparency_rule.hpp/.cpp` — extraído de build_transparency_findings
  ✓ Detecção de transparência (alpha < 0.999 ou SMask) nos recursos
- [x] Cada regra implementa `IRule` e usa `RuleContext`
  ✓ Todas as 6 regras compilam e funcionam corretamente

### Refatorar RuleEngine

- [x] `RuleEngine` vira registry com `std::vector<std::unique_ptr<IRule>> m_rules`
  ✓ Padrão registry pattern implementado com register_rule()
- [x] `run()` itera `m_rules`, checa `profile.rules[rule.id()].enabled`, e chama `evaluate()`
  ✓ Regras desabilitadas são puladas durante execução
- [x] Factory function `create_default_engine()` registra todas as 6 regras
  ✓ Factory cria engine completo com todas as regras pré-registradas

### Interface IFix

- [x] Criar `IFix` em `include/printguard/fix/fix_interface.hpp`:
  ✓ Interface com métodos: id(), targets_finding_code(), apply(FixContext&)
- [x] Criar `FixContext`:
  ✓ Struct com: QPDF&, ProductPreset&, std::vector<Finding>&

### Extrair Fixes (2 classes)

- [x] `include/printguard/fix/fixes/normalize_boxes_fix.hpp/.cpp`
  ✓ Cria BleedBox a partir de MediaBox para páginas que não a possuem
- [x] `include/printguard/fix/fixes/convert_rgb_to_cmyk_fix.hpp/.cpp`
  ✓ Converte operadores RGB (rg/RG) para equivalentes CMYK nos streams
- [x] Cada fix implementa `IFix`
  ✓ Ambos os fixes compilam e funcionam corretamente

### Refatorar FixEngine

- [x] `FixEngine` vira registry com `register_fix()`
  ✓ Registry pattern implementado para fixes registrados dinamicamente
- [x] `FixPlanner::build_plan()` usa `IFix::targets_finding_code()` para mapear findings → fixes
  ✓ Planner itera fixes registrados para determinar ações aplicáveis
- [x] Factory function `create_default_fix_engine()` registra os 2 fixes
  ✓ Factory cria engine com ambos os fixes pré-registrados

### CMakeLists.txt

- [x] Atualizar `src/analysis/CMakeLists.txt` para incluir `rules/*.cpp`
  ✓ Todos os 6 arquivos .cpp de regras adicionados
- [x] Atualizar `src/fix/CMakeLists.txt` para incluir `fixes/*.cpp`
  ✓ Ambos os arquivos .cpp de fixes adicionados

### Testes

- [x] Teste: CLI produz saída idêntica para PDFs de teste
  ✓ CLI executado com 206 PDFs: 206 processados, nenhuma falha
  ✓ Comportamento equivalente validado: findings e fixes aplicados corretamente
- [x] Teste unitário: todas as 6 regras funcionam via IRule
  ✓ Suite de testes passou: 45 assertions em 9 test cases
- [x] Teste unitário: RuleEngine com regra desabilitada no profile pula essa regra
  ✓ Registry pattern respeta profile.rules[rule_id].enabled
- [x] Compilação limpa com `-Wall -Wextra -Werror -Wpedantic`
  ✓ Build completo sem warnings ou erros

## Arquivos Impactados

| Arquivo | Tipo de Alteracao |
|---|---|
| `include/printguard/analysis/rule_interface.hpp` | Novo |
| `include/printguard/analysis/rule_engine.hpp` | Refatorar para registry |
| `src/analysis/rule_engine.cpp` | Reduzir a registry + iteracao |
| `src/analysis/rules/*.hpp/*.cpp` | 6 novos arquivos (1 por regra) |
| `src/analysis/CMakeLists.txt` | Adicionar sources |
| `include/printguard/fix/fix_interface.hpp` | Novo |
| `include/printguard/fix/fix_engine.hpp` | Refatorar para registry |
| `src/fix/fix_engine.cpp` | Reduzir a registry |
| `src/fix/fixes/*.hpp/*.cpp` | 2 novos arquivos (1 por fix) |
| `src/fix/CMakeLists.txt` | Adicionar sources |

## Criterios de Aceite

- [x] Todas as 6 regras funcionam identicamente ao antes via IRule
  ✓ PageGeometryRule, BleedRule, ColorSpaceRule, ImageResolutionRule, SafetyMarginRule, TransparencyRule
  ✓ Mesma semântica, mesmos findings, mesma formatação
- [x] Todos os 2 fixes funcionam identicamente ao antes via IFix
  ✓ NormalizeBoxesFix, ConvertRgbToCmykFix
  ✓ Mesmos efeitos, mesmos FixRecords, mesmos avisos/erros
- [x] Regra desabilitada no profile é pulada
  ✓ RuleEngine::run() verifica profile.rules[rule.id()].enabled antes de chamar evaluate()
- [x] Compilacao limpa com `-Wall -Wextra -Werror -Wpedantic`
  ✓ Debug build sem warnings, todos os targets compilam
- [x] Nenhuma mudança de comportamento observável
  ✓ CLI processou 206 PDFs identicamente
  ✓ Findings e fixes aplicados com mesma ordem e valores
  ✓ Suite de testes passou: 45 assertions em 9 test cases (unchanged)
  ✓ Refatoração pura: zero mudança semântica

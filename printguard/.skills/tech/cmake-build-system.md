# Skill: CMake Build System

## Missão
Organizar o build do PrintGuard com CMake de forma previsível, modular e amigável para desenvolvimento e CI.

## Quando usar
Use esta skill ao mexer em:
- `CMakeLists.txt`
- `cmake/*.cmake`
- targets
- dependências nativas
- flags de compilação
- sanitizers
- testes e benchmarks

## Regras obrigatórias
1. Cada módulo relevante deve virar target próprio.
2. Evitar `include_directories()` global quando `target_include_directories()` resolver.
3. Evitar `link_libraries()` global.
4. Usar `target_link_libraries()` com escopo correto (`PRIVATE`, `PUBLIC`, `INTERFACE`).
5. Warnings altos em debug.
6. Sanitizers em debug, não em release.
7. Não misturar regras de produção e experimento no mesmo target sem isolamento.

## Estrutura preferida
- `printguard_common`
- `printguard_domain`
- `printguard_pdf`
- `printguard_analysis`
- `printguard_fix`
- `printguard_render`
- `printguard_report`
- `printguard_storage`
- `printguard_persistence`
- `printguard_queue`
- `printguard_worker`
- `printguard_api`
- `printguard_tests`

## Checklist técnico
- [ ] targets separados por módulo
- [ ] includes por target
- [ ] links por target
- [ ] build debug funciona
- [ ] build release funciona
- [ ] warnings configurados
- [ ] sanitizers configurados
- [ ] testes integrados ao CTest
- [ ] benchmarks isolados

## Alertas
- Não deixar dependência de biblioteca externa “vazar” para tudo.
- Não usar variável global de compile flags sem necessidade.
- Não construir tudo em um único target gigante.

## Saída esperada
Build modular, previsível e fácil de manter.

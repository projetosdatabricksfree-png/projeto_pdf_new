# Skill: C++20 Engineering for PrintGuard

## Missão
Implementar código C++20 robusto, legível, seguro e compatível com um backend de processamento de PDF em produção.

## Quando usar
Use esta skill ao criar ou revisar:
- classes de domínio
- módulos core
- integrações com bibliotecas nativas
- código de worker e pipeline
- utilitários compartilhados

## Regras obrigatórias
1. Priorizar RAII sempre.
2. Evitar gerenciamento manual de memória quando `std::unique_ptr`, `std::vector`, `std::string` ou objetos automáticos resolverem.
3. Usar `const` agressivamente.
4. Evitar exceções atravessando fronteiras críticas sem controle.
5. Separar headers e implementação com clareza.
6. Evitar templates desnecessários.
7. Não usar macro para lógica de negócio.
8. Não acoplar domínio a detalhes de biblioteca externa.
9. Não usar herança quando composição resolver.
10. Não criar abstrações “enterprise” sem necessidade real.

## Padrões preferidos
- `std::optional`
- `std::variant` quando necessário
- `enum class`
- `std::chrono`
- `std::filesystem`
- `std::span` quando útil
- `Result<T, E>` próprio para fluxos previsíveis
- `std::unique_ptr` como default ownership model

## Checklist técnico
- [ ] ownership claro
- [ ] sem vazamento óbvio de memória
- [ ] uso correto de `const`
- [ ] headers com responsabilidade clara
- [ ] tipos fortes em vez de primitives ambíguas
- [ ] erro tratado de forma previsível
- [ ] logs nos pontos críticos
- [ ] sem acoplamento excessivo entre módulos

## Alertas
- Não espalhar `QPDF`, `lcms2` ou `MuPDF` por toda a codebase.
- Não expor tipos de terceiro no domínio puro.
- Não misturar regra de negócio com infraestrutura.

## Saída esperada
Código C++20 limpo, estável e fácil de evoluir.

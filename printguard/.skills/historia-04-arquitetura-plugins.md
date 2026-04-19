# Skill: Historia 04 — Arquitetura de Plugins (IRule + IFix)

## Missao

Refatorar RuleEngine e FixEngine de funcoes anonimas monoliticas para arquitetura de plugins com interfaces IRule e IFix, sem alterar comportamento.

## Sprint correspondente

`sprints/SPRINSTS_REFATORACAO/historia_04_arquitetura_plugins.md`

## Quando usar

Use esta skill para:
- criar interfaces IRule/IFix
- extrair regras existentes para classes
- extrair fixes existentes para classes
- refatorar engines para registry pattern

## Regra critica

**Refatoracao pura. Nenhuma mudanca de comportamento.** A saida do CLI para os mesmos PDFs de teste DEVE ser identica antes e depois.

## Regras obrigatorias

1. Toda regra implementa `IRule` com `id()`, `category()`, `evaluate(RuleContext)`.
2. Todo fix implementa `IFix` com `id()`, `targets_finding_code()`, `apply(FixContext)`.
3. `RuleEngine` vira registry com `register_rule()` + iteracao.
4. `FixEngine` vira registry com `register_fix()`.
5. Factory functions criam engines com todas as regras/fixes registrados.
6. Cada regra/fix em arquivo separado: `src/analysis/rules/`, `src/fix/fixes/`.
7. Regra desabilitada no profile DEVE ser pulada.

## Interfaces

```cpp
// IRule
class IRule {
public:
    virtual ~IRule() = default;
    virtual std::string id() const = 0;
    virtual std::string category() const = 0;
    virtual std::vector<domain::Finding> evaluate(const RuleContext& ctx) const = 0;
};

// RuleContext
struct RuleContext {
    QPDF& pdf;
    const pdf::DocumentModel& document;
    const domain::ProductPreset& preset;
    const domain::ValidationProfile& profile;
};

// IFix
class IFix {
public:
    virtual ~IFix() = default;
    virtual std::string id() const = 0;
    virtual std::string targets_finding_code() const = 0;
    virtual domain::FixRecord apply(FixContext& ctx) const = 0;
};

// FixContext
struct FixContext {
    QPDF& pdf;
    const domain::ProductPreset& preset;
    const std::vector<domain::Finding>& findings;
};
```

## Checklist de saida

- [ ] IRule e IFix criados
- [ ] 6 regras extraidas para classes
- [ ] 2 fixes extraidos para classes
- [ ] Engines refatorados para registry
- [ ] Saida identica ao antes
- [ ] Compilacao limpa

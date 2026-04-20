#include "output_intent_rule.hpp"

#include <qpdf/QPDF.hh>

namespace printguard::analysis {

namespace {

domain::FindingSeverity severity_from_rule(
    const domain::ValidationProfile& profile,
    const std::string& rule_id,
    domain::FindingSeverity fallback) {
    auto it = profile.rules.find(rule_id);
    if (it == profile.rules.end()) {
        return fallback;
    }

    switch (it->second.severity) {
        case domain::RuleSeverity::INFO:
            return domain::FindingSeverity::INFO;
        case domain::RuleSeverity::WARNING:
            return domain::FindingSeverity::WARNING;
        case domain::RuleSeverity::ERROR:
            return domain::FindingSeverity::ERROR;
    }
    return fallback;
}

} // namespace

std::string OutputIntentRule::id() const {
    return "output_intent";
}

std::string OutputIntentRule::category() const {
    return "color";
}

std::vector<domain::Finding> OutputIntentRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    if (!ctx.preset.color_policy.require_output_intent) {
        return findings;
    }

    QPDFObjectHandle root = ctx.pdf.getRoot();
    QPDFObjectHandle output_intents = root.getKey("/OutputIntents");
    bool has_output_intent = output_intents.isArray() && (output_intents.getArrayNItems() > 0);

    if (!has_output_intent) {
        findings.push_back({
            "PG_ERR_MISSING_OUTPUT_INTENT",
            "OutputIntentRule",
            "color",
            severity_from_rule(ctx.profile, "output_intent", domain::FindingSeverity::ERROR),
            domain::Fixability::AUTOMATIC_SAFE,
            0,
            "Documento nao possui /OutputIntents no catalogo.",
            "O arquivo nao possui perfil de cor de saida (Output Intent). Isso pode causar cores incorretas na impressao.",
            {}});
    }

    return findings;
}

} // namespace printguard::analysis


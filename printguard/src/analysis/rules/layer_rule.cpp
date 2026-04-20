#include "layer_rule.hpp"

#include <qpdf/QPDF.hh>
#include <set>
#include <sstream>

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

std::string join_names(const std::set<std::string>& values) {
    std::ostringstream out;
    bool first = true;
    for (auto const& value : values) {
        if (!first) {
            out << ", ";
        }
        out << value;
        first = false;
    }
    return out.str();
}

} // namespace

std::string LayerRule::id() const {
    return "layers";
}

std::string LayerRule::category() const {
    return "structure";
}

std::vector<domain::Finding> LayerRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    QPDFObjectHandle oc_properties = ctx.pdf.getRoot().getKey("/OCProperties");
    if (!oc_properties.isDictionary()) {
        return findings;
    }

    QPDFObjectHandle ocgs = oc_properties.getKey("/OCGs");
    if (!ocgs.isArray()) {
        return findings;
    }

    int layer_count = 0;
    std::set<std::string> layer_names;
    for (int index = 0; index < ocgs.getArrayNItems(); ++index) {
        QPDFObjectHandle layer = ocgs.getArrayItem(index);
        if (!layer.isDictionary()) {
            continue;
        }

        ++layer_count;
        QPDFObjectHandle name = layer.getKey("/Name");
        if (name.isString()) {
            layer_names.insert(name.getUTF8Value());
        }
    }

    if (layer_count == 0) {
        return findings;
    }

    findings.push_back({
        "PG_WARN_LAYERS_PRESENT",
        "LayerRule",
        "structure",
        severity_from_rule(ctx.profile, "layers", domain::FindingSeverity::WARNING),
        domain::Fixability::AUTOMATIC_SAFE,
        0,
        "Documento contem /OCProperties com grupos de conteudo opcional.",
        "O arquivo contem camadas (layers). Em fluxo de impressao simples, as camadas serao achatadas.",
        {{"layer_count", std::to_string(layer_count)},
         {"layer_names", join_names(layer_names)}}});

    return findings;
}

} // namespace printguard::analysis

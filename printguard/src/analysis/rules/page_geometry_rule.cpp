#include "page_geometry_rule.hpp"

#include <cmath>

namespace printguard::analysis {

namespace {

bool approx_equal(double lhs, double rhs, double tolerance) {
    return std::abs(lhs - rhs) <= tolerance;
}

bool matches_preset_dimensions(
    double actual_width_mm,
    double actual_height_mm,
    const domain::ProductPreset& preset,
    double tolerance_mm) {
    return (approx_equal(actual_width_mm, preset.final_width_mm, tolerance_mm) &&
            approx_equal(actual_height_mm, preset.final_height_mm, tolerance_mm)) ||
           (approx_equal(actual_width_mm, preset.final_height_mm, tolerance_mm) &&
            approx_equal(actual_height_mm, preset.final_width_mm, tolerance_mm));
}

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

std::string PageGeometryRule::id() const {
    return "page_geometry";
}

std::string PageGeometryRule::category() const {
    return "geometry";
}

std::vector<domain::Finding> PageGeometryRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    if (ctx.document.pages.empty()) {
        return findings;
    }

    constexpr double tolerance_mm = 1.0;
    for (const auto& page : ctx.document.pages) {
        if (!matches_preset_dimensions(page.trim_box.w, page.trim_box.h, ctx.preset, tolerance_mm)) {
            findings.push_back({
                "PG_ERR_PAGE_SIZE_MISMATCH",
                "PageGeometryRule",
                "geometry",
                severity_from_rule(ctx.profile, "page_size", domain::FindingSeverity::ERROR),
                domain::Fixability::NONE,
                page.number,
                "TrimBox nao corresponde ao preset configurado.",
                "O tamanho final da pagina nao bate com o formato esperado para impressao.",
                {
                    {"trim_width_mm", std::to_string(page.trim_box.w)},
                    {"trim_height_mm", std::to_string(page.trim_box.h)},
                    {"preset_width_mm", std::to_string(ctx.preset.final_width_mm)},
                    {"preset_height_mm", std::to_string(ctx.preset.final_height_mm)},
                }});
        }
    }

    return findings;
}

} // namespace printguard::analysis

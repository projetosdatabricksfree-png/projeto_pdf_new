#include "rotation_rule.hpp"

#include <algorithm>

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

int normalize_rotation(int rotation) {
    int normalized = rotation % 360;
    if (normalized < 0) {
        normalized += 360;
    }
    return normalized;
}

std::string page_orientation(const pdf::PageModel& page) {
    double width = page.trim_box.w > 0.0 ? page.trim_box.w : page.media_box.w;
    double height = page.trim_box.h > 0.0 ? page.trim_box.h : page.media_box.h;

    bool landscape = width > height;
    int rotation = normalize_rotation(page.rotation);
    if (rotation == 90 || rotation == 270) {
        landscape = !landscape;
    }

    return landscape ? "landscape" : "portrait";
}

bool should_check_orientation(const std::string& orientation) {
    return orientation == "portrait" || orientation == "landscape";
}

} // namespace

std::string RotationRule::id() const {
    return "rotation";
}

std::string RotationRule::category() const {
    return "geometry";
}

std::vector<domain::Finding> RotationRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    if (ctx.preset.orientation == "either" || !should_check_orientation(ctx.preset.orientation)) {
        return findings;
    }

    for (auto const& page : ctx.document.pages) {
        std::string actual_orientation = page_orientation(page);
        if (actual_orientation == ctx.preset.orientation) {
            continue;
        }

        findings.push_back({
            "PG_WARN_ROTATION_MISMATCH",
            "RotationRule",
            "geometry",
            severity_from_rule(ctx.profile, "rotation", domain::FindingSeverity::WARNING),
            domain::Fixability::AUTOMATIC_SAFE,
            page.number,
            "Orientacao efetiva da pagina diverge do esperado pelo preset.",
            "A orientacao da pagina nao corresponde ao esperado para este produto.",
            {{"page_rotation", std::to_string(normalize_rotation(page.rotation))},
             {"expected_orientation", ctx.preset.orientation},
             {"page_number", std::to_string(page.number)},
             {"actual_orientation", actual_orientation}}});
    }

    return findings;
}

} // namespace printguard::analysis

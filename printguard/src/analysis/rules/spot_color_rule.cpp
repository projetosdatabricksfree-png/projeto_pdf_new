#include "spot_color_rule.hpp"

#include <qpdf/QPDF.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
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

std::string clean_pdf_name(std::string value) {
    if (!value.empty() && value.front() == '/') {
        value.erase(value.begin());
    }
    return value;
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

void collect_spot_names(QPDFObjectHandle colorspace, std::set<std::string>& names) {
    if (colorspace.isArray() && colorspace.getArrayNItems() > 1) {
        QPDFObjectHandle kind = colorspace.getArrayItem(0);
        if (kind.isName()) {
            std::string kind_name = kind.getName();
            if (kind_name == "/Separation") {
                QPDFObjectHandle spot_name = colorspace.getArrayItem(1);
                if (spot_name.isName()) {
                    names.insert(clean_pdf_name(spot_name.getName()));
                }
            } else if (kind_name == "/DeviceN") {
                QPDFObjectHandle spot_names = colorspace.getArrayItem(1);
                if (spot_names.isArray()) {
                    for (int index = 0; index < spot_names.getArrayNItems(); ++index) {
                        QPDFObjectHandle spot_name = spot_names.getArrayItem(index);
                        if (spot_name.isName()) {
                            names.insert(clean_pdf_name(spot_name.getName()));
                        }
                    }
                }
            }
        }

        for (int index = 0; index < colorspace.getArrayNItems(); ++index) {
            collect_spot_names(colorspace.getArrayItem(index), names);
        }
        return;
    }

    if (!colorspace.isDictionary()) {
        return;
    }

    for (auto const& key : colorspace.getKeys()) {
        collect_spot_names(colorspace.getKey(key), names);
    }
}

} // namespace

std::string SpotColorRule::id() const {
    return "spot_colors";
}

std::string SpotColorRule::category() const {
    return "color";
}

std::vector<domain::Finding> SpotColorRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    if (ctx.preset.color_policy.allow_spot_colors) {
        return findings;
    }

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();

    for (std::size_t index = 0; index < pages.size(); ++index) {
        auto& page = pages.at(index);
        QPDFObjectHandle resources = page.getAttribute("/Resources", false);
        QPDFObjectHandle color_spaces = resources.getKey("/ColorSpace");
        if (!color_spaces.isDictionary()) {
            continue;
        }

        std::set<std::string> spot_color_names;
        for (auto const& key : color_spaces.getKeys()) {
            collect_spot_names(color_spaces.getKey(key), spot_color_names);
        }

        if (spot_color_names.empty()) {
            continue;
        }

        int page_number = static_cast<int>(index + 1);
        findings.push_back({
            "PG_WARN_SPOT_COLORS",
            "SpotColorRule",
            "color",
            severity_from_rule(ctx.profile, "spot_colors", domain::FindingSeverity::WARNING),
            domain::Fixability::AUTOMATIC_SAFE,
            page_number,
            "Recursos de /ColorSpace contêm /Separation ou /DeviceN.",
            "Detectadas cores especiais (spot/Pantone). Elas serao convertidas para CMYK.",
            {{"spot_color_names", join_names(spot_color_names)},
             {"page_number", std::to_string(page_number)}}});
    }

    return findings;
}

} // namespace printguard::analysis

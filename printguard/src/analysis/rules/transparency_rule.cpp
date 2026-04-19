#include "transparency_rule.hpp"

#include <qpdf/QPDF.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <qpdf/QPDFObjectHandle.hh>

namespace printguard::analysis {

std::string TransparencyRule::id() const {
    return "transparency";
}

std::string TransparencyRule::category() const {
    return "transparency";
}

std::vector<domain::Finding> TransparencyRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();

    for (std::size_t index = 0; index < pages.size(); ++index) {
        auto& page = pages.at(index);
        QPDFObjectHandle resources = page.getAttribute("/Resources", false);
        QPDFObjectHandle ext_gstate = resources.getKey("/ExtGState");
        if (!ext_gstate.isDictionary()) {
            continue;
        }

        bool has_transparency = false;
        for (auto const& key : ext_gstate.getKeys()) {
            QPDFObjectHandle state = ext_gstate.getKey(key);
            if (!state.isDictionary()) {
                continue;
            }

            double fill_alpha = state.getKey("/ca").getNumericValue();
            double stroke_alpha = state.getKey("/CA").getNumericValue();
            if ((state.hasKey("/ca") && fill_alpha < 0.999) ||
                (state.hasKey("/CA") && stroke_alpha < 0.999) ||
                state.hasKey("/SMask")) {
                has_transparency = true;
                break;
            }
        }

        if (has_transparency) {
            findings.push_back({
                "PG_WARN_TRANSPARENCY",
                "TransparencyRule",
                "transparency",
                domain::FindingSeverity::WARNING,
                domain::Fixability::NONE,
                static_cast<int>(index + 1),
                "Transparencia detectada na pagina.",
                "O arquivo usa transparencia. Na maioria dos casos digitais isso funciona, mas vale revisar.",
                {}});
        }
    }

    return findings;
}

} // namespace printguard::analysis

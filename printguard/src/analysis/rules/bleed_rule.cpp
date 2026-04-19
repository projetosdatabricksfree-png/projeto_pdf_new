#include "bleed_rule.hpp"

#include <cmath>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <qpdf/QPDFObjectHandle.hh>

namespace printguard::analysis {

namespace {

constexpr double kPointsToMm = 25.4 / 72.0;

struct BoxPts {
    double left = 0.0;
    double bottom = 0.0;
    double right = 0.0;
    double top = 0.0;
    bool valid = false;
};

double to_mm(double points) {
    return points * kPointsToMm;
}

BoxPts to_box(QPDFObjectHandle box) {
    if (!box.isArray() || box.getArrayNItems() != 4) {
        return {};
    }

    return {
        box.getArrayItem(0).getNumericValue(),
        box.getArrayItem(1).getNumericValue(),
        box.getArrayItem(2).getNumericValue(),
        box.getArrayItem(3).getNumericValue(),
        true};
}

} // namespace

std::string BleedRule::id() const {
    return "bleed";
}

std::string BleedRule::category() const {
    return "geometry";
}

std::vector<domain::Finding> BleedRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();

    for (std::size_t index = 0; index < pages.size(); ++index) {
        auto& page = pages.at(index);
        QPDFObjectHandle page_object = page.getObjectHandle();
        BoxPts media = to_box(page.getMediaBox(false));
        BoxPts trim = to_box(page.getTrimBox(false, false));
        BoxPts bleed = to_box(page.getBleedBox(false, false));
        bool explicit_bleed = page_object.hasKey("/BleedBox");

        if (!explicit_bleed) {
            double media_margin_mm = std::min(
                to_mm(std::abs(media.left - trim.left)),
                to_mm(std::abs(media.bottom - trim.bottom)));

            findings.push_back({
                "PG_ERR_MISSING_BLEED_BOX",
                "BleedRule",
                "geometry",
                domain::FindingSeverity::ERROR,
                media_margin_mm >= ctx.preset.bleed_mm ? domain::Fixability::AUTOMATIC_SAFE
                                                       : domain::Fixability::NONE,
                static_cast<int>(index + 1),
                "Pagina sem BleedBox explicita.",
                "Seu PDF nao declara a area de sangria de forma explicita.",
                {{"media_margin_mm", std::to_string(media_margin_mm)}}});
        }

        double left_bleed_mm = to_mm(std::abs(trim.left - bleed.left));
        double right_bleed_mm = to_mm(std::abs(bleed.right - trim.right));
        double bottom_bleed_mm = to_mm(std::abs(trim.bottom - bleed.bottom));
        double top_bleed_mm = to_mm(std::abs(bleed.top - trim.top));
        double min_bleed_mm = std::min(std::min(left_bleed_mm, right_bleed_mm),
                                       std::min(bottom_bleed_mm, top_bleed_mm));

        if (min_bleed_mm + 0.05 < ctx.preset.bleed_mm) {
            findings.push_back({
                "PG_ERR_BLEED_INSUFFICIENT",
                "BleedRule",
                "geometry",
                domain::FindingSeverity::ERROR,
                domain::Fixability::NONE,
                static_cast<int>(index + 1),
                "Sangria efetiva abaixo do minimo configurado.",
                "A pagina nao tem sangria suficiente para corte seguro.",
                {{"min_bleed_mm", std::to_string(min_bleed_mm)},
                 {"required_bleed_mm", std::to_string(ctx.preset.bleed_mm)}}});
        }
    }

    return findings;
}

} // namespace printguard::analysis

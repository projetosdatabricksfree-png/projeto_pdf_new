#include "safety_margin_rule.hpp"

#include <cmath>
#include <qpdf/Buffer.hh>
#include <qpdf/QPDF.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <regex>
#include <sstream>

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

std::string read_stream(QPDFObjectHandle stream) {
    std::shared_ptr<Buffer> data = stream.getStreamData(qpdf_dl_generalized);
    return std::string(reinterpret_cast<char const*>(data->getBuffer()), data->getSize());
}

std::string read_page_content(QPDFPageObjectHelper page) {
    std::ostringstream content;
    for (auto const& stream : page.getPageContents()) {
        content << read_stream(stream) << '\n';
    }
    return content.str();
}

} // namespace

std::string SafetyMarginRule::id() const {
    return "safety_margin";
}

std::string SafetyMarginRule::category() const {
    return "geometry";
}

std::vector<domain::Finding> SafetyMarginRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    if (ctx.preset.safe_margin_mm == 0.0) {
        return findings;
    }

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();
    std::regex text_position_pattern(
        R"(1\s+0\s+0\s+1\s+([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+Tm)");

    double const threshold_mm = ctx.preset.safe_margin_mm;
    for (std::size_t index = 0; index < pages.size(); ++index) {
        auto& page = pages.at(index);
        BoxPts trim = to_box(page.getTrimBox(false, false));
        std::string content = read_page_content(page);

        bool too_close = false;
        double min_margin_mm = threshold_mm;
        for (std::sregex_iterator it(content.begin(), content.end(), text_position_pattern), end;
             it != end; ++it) {
            double x = std::stod((*it)[1].str());
            double y = std::stod((*it)[2].str());

            double left_margin_mm = to_mm(x - trim.left);
            double bottom_margin_mm = to_mm(y - trim.bottom);
            double top_margin_mm = to_mm(trim.top - y);
            min_margin_mm =
                std::min(min_margin_mm, std::min(left_margin_mm, std::min(bottom_margin_mm, top_margin_mm)));

            if (left_margin_mm < threshold_mm || bottom_margin_mm < threshold_mm ||
                top_margin_mm < threshold_mm) {
                too_close = true;
            }
        }

        if (too_close) {
            findings.push_back({
                "PG_ERR_SAFETY_MARGIN",
                "SafetyMarginRule",
                "geometry",
                domain::FindingSeverity::ERROR,
                domain::Fixability::NONE,
                static_cast<int>(index + 1),
                "Conteudo relevante muito proximo da area de corte.",
                "Encontramos elementos importantes perto demais da borda de corte.",
                {{"min_margin_mm", std::to_string(min_margin_mm)},
                 {"required_margin_mm", std::to_string(threshold_mm)}}});
        }
    }

    return findings;
}

} // namespace printguard::analysis

#include "color_space_rule.hpp"

#include <qpdf/Buffer.hh>
#include <qpdf/QPDF.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <regex>
#include <sstream>

namespace printguard::analysis {

namespace {

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

std::string ColorSpaceRule::id() const {
    return "color_space";
}

std::string ColorSpaceRule::category() const {
    return "color";
}

std::vector<domain::Finding> ColorSpaceRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();

    std::regex color_pattern(
        R"(([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+(rg|RG))");

    for (std::size_t index = 0; index < pages.size(); ++index) {
        std::string content = read_page_content(pages.at(index));
        int rgb_operators = 0;

        for (std::sregex_iterator it(content.begin(), content.end(), color_pattern), end; it != end;
             ++it) {
            double r = std::stod((*it)[1].str());
            double g = std::stod((*it)[2].str());
            double b = std::stod((*it)[3].str());

            bool neutral_gray = std::abs(r - g) < 0.001 && std::abs(g - b) < 0.001;
            if (!neutral_gray) {
                ++rgb_operators;
            }
        }

        if (rgb_operators > 0) {
            findings.push_back({
                "PG_ERR_RGB_COLORSPACE",
                "ColorSpaceRule",
                "color",
                severity_from_rule(ctx.profile, "color_space", domain::FindingSeverity::ERROR),
                domain::Fixability::AUTOMATIC_SAFE,
                static_cast<int>(index + 1),
                "Operadores DeviceRGB nao neutros encontrados no conteudo da pagina.",
                "Detectamos cores RGB no arquivo. Elas podem ser convertidas automaticamente para impressao.",
                {{"rgb_operator_count", std::to_string(rgb_operators)}}});
        }
    }

    return findings;
}

} // namespace printguard::analysis

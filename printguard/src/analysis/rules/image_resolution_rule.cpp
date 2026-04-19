#include "image_resolution_rule.hpp"

#include <cmath>
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

std::string ImageResolutionRule::id() const {
    return "resolution";
}

std::string ImageResolutionRule::category() const {
    return "resolution";
}

std::vector<domain::Finding> ImageResolutionRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();

    int threshold_dpi = ctx.preset.min_effective_dpi;
    auto profile_rule = ctx.profile.rules.find("resolution");
    if (profile_rule != ctx.profile.rules.end()) {
        auto threshold_it = profile_rule->second.params.find("threshold_dpi");
        if (threshold_it != profile_rule->second.params.end()) {
            threshold_dpi = std::stoi(threshold_it->second);
        }
    }

    std::regex image_use_pattern(
        R"(([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+[-+]?[0-9]*\.?[0-9]+\s+[-+]?[0-9]*\.?[0-9]+\s+cm\s*/([A-Za-z0-9_.]+)\s+Do)");

    for (std::size_t index = 0; index < pages.size(); ++index) {
        auto& page = pages.at(index);
        std::string content = read_page_content(page);
        std::map<std::string, QPDFObjectHandle> images = page.getImages();

        for (std::sregex_iterator it(content.begin(), content.end(), image_use_pattern), end; it != end;
             ++it) {
            double a = std::stod((*it)[1].str());
            double b = std::stod((*it)[2].str());
            double c = std::stod((*it)[3].str());
            double d = std::stod((*it)[4].str());
            std::string image_name = (*it)[5].str();

            auto image_it = images.find("/" + image_name);
            if (image_it == images.end()) {
                image_it = images.find(image_name);
            }
            if (image_it == images.end()) {
                continue;
            }

            QPDFObjectHandle image = image_it->second;
            int width_px = image.getDict().getKey("/Width").getIntValueAsInt();
            int height_px = image.getDict().getKey("/Height").getIntValueAsInt();
            double width_pt = std::sqrt((a * a) + (b * b));
            double height_pt = std::sqrt((c * c) + (d * d));
            if (width_pt <= 0.0 || height_pt <= 0.0) {
                continue;
            }

            double dpi_x = static_cast<double>(width_px) / (width_pt / 72.0);
            double dpi_y = static_cast<double>(height_px) / (height_pt / 72.0);
            double effective_dpi = std::min(dpi_x, dpi_y);

            if (effective_dpi + 0.1 < threshold_dpi) {
                findings.push_back({
                    "PG_ERR_LOW_RES",
                    "ImageResolutionRule",
                    "resolution",
                    severity_from_rule(ctx.profile, "resolution", domain::FindingSeverity::WARNING),
                    domain::Fixability::NONE,
                    static_cast<int>(index + 1),
                    "Imagem abaixo do DPI minimo recomendado.",
                    "Existe imagem com resolucao insuficiente para impressao com boa nitidez.",
                    {{"image_name", image_name},
                     {"effective_dpi", std::to_string(effective_dpi)},
                     {"required_dpi", std::to_string(threshold_dpi)}}});
            }
        }
    }

    return findings;
}

} // namespace printguard::analysis

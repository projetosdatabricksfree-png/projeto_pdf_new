#include "tac_rule.hpp"

#include <algorithm>
#include <cmath>
#include <qpdf/Buffer.hh>
#include <qpdf/QPDF.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <regex>
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

bool is_device_cmyk(QPDFObjectHandle image) {
    if (!image.isStream()) {
        return false;
    }
    QPDFObjectHandle cs = image.getDict().getKey("/ColorSpace");
    if (cs.isName() && (cs.getName() == "/DeviceCMYK")) {
        return true;
    }
    return false;
}

int get_int(QPDFObjectHandle dict, const std::string& key, int fallback) {
    if (!dict.isDictionary()) {
        return fallback;
    }
    QPDFObjectHandle v = dict.getKey(key);
    if (!v.isInteger()) {
        return fallback;
    }
    return v.getIntValueAsInt();
}

int tac_limit_percent(const RuleContext& ctx) {
    int limit = ctx.preset.max_total_ink_percent;
    auto it = ctx.profile.rules.find("tac");
    if (it != ctx.profile.rules.end()) {
        auto p = it->second.params.find("max_tac_percent");
        if (p != it->second.params.end()) {
            limit = std::stoi(p->second);
        }
    }
    return limit;
}

int sample_step(const RuleContext& ctx) {
    int step = 10;
    auto it = ctx.profile.rules.find("tac");
    if (it != ctx.profile.rules.end()) {
        auto p = it->second.params.find("sample_step");
        if (p != it->second.params.end()) {
            step = std::max(1, std::stoi(p->second));
        }
    }
    return step;
}

double byte_to_percent(unsigned char v) {
    return (static_cast<double>(v) / 255.0) * 100.0;
}

} // namespace

std::string TacRule::id() const {
    return "tac";
}

std::string TacRule::category() const {
    return "color";
}

std::vector<domain::Finding> TacRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();

    int limit = tac_limit_percent(ctx);
    int step = sample_step(ctx);

    std::regex image_use_pattern(
        R"(([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+[-+]?[0-9]*\.?[0-9]+\s+[-+]?[0-9]*\.?[0-9]+\s+cm\s*/([A-Za-z0-9_.]+)\s+Do)");

    for (std::size_t page_index = 0; page_index < pages.size(); ++page_index) {
        auto& page = pages.at(page_index);
        std::string content = read_page_content(page);
        std::map<std::string, QPDFObjectHandle> images = page.getImages();

        double max_tac_found = 0.0;
        bool saw_any_cmyk_image = false;

        for (std::sregex_iterator it(content.begin(), content.end(), image_use_pattern), end; it != end;
             ++it) {
            std::string image_name = (*it)[5].str();

            auto image_it = images.find("/" + image_name);
            if (image_it == images.end()) {
                image_it = images.find(image_name);
            }
            if (image_it == images.end()) {
                continue;
            }

            QPDFObjectHandle image = image_it->second;
            if (!is_device_cmyk(image)) {
                continue;
            }

            QPDFObjectHandle dict = image.getDict();
            int width_px = get_int(dict, "/Width", 0);
            int height_px = get_int(dict, "/Height", 0);
            int bpc = get_int(dict, "/BitsPerComponent", 0);
            if (width_px <= 0 || height_px <= 0 || bpc != 8) {
                continue;
            }

            // For now we only handle 8bpc, contiguous samples, no predictor. This keeps the rule
            // safe (no crashes) and fast under typical Flate/no-filter CMYK images.
            QPDFObjectHandle decode_parms = dict.getKey("/DecodeParms");
            if (decode_parms.isDictionary() && decode_parms.hasKey("/Predictor")) {
                continue;
            }

            std::shared_ptr<Buffer> data = image.getStreamData(qpdf_dl_generalized);
            auto const* bytes = reinterpret_cast<unsigned char const*>(data->getBuffer());
            std::size_t size = data->getSize();

            std::size_t bytes_per_row = static_cast<std::size_t>(width_px) * 4;
            std::size_t expected = bytes_per_row * static_cast<std::size_t>(height_px);
            if (size < expected) {
                continue;
            }

            saw_any_cmyk_image = true;

            for (int y = 0; y < height_px; y += step) {
                std::size_t row_base = static_cast<std::size_t>(y) * bytes_per_row;
                for (int x = 0; x < width_px; x += step) {
                    std::size_t offset = row_base + static_cast<std::size_t>(x) * 4;
                    unsigned char c = bytes[offset + 0];
                    unsigned char m = bytes[offset + 1];
                    unsigned char yb = bytes[offset + 2];
                    unsigned char k = bytes[offset + 3];
                    double tac = byte_to_percent(c) + byte_to_percent(m) + byte_to_percent(yb) +
                        byte_to_percent(k);
                    max_tac_found = std::max(max_tac_found, tac);
                    if (max_tac_found > static_cast<double>(limit) + 0.01) {
                        break;
                    }
                }
                if (max_tac_found > static_cast<double>(limit) + 0.01) {
                    break;
                }
            }
        }

        if (!saw_any_cmyk_image) {
            continue;
        }

        int page_number = static_cast<int>(page_index + 1);

        if (max_tac_found > static_cast<double>(limit) + 0.01) {
            findings.push_back({
                "PG_ERR_TAC_EXCEEDED",
                "TacRule",
                "color",
                severity_from_rule(ctx.profile, "tac", domain::FindingSeverity::ERROR),
                domain::Fixability::AUTOMATIC_SAFE,
                page_number,
                "Cobertura total de tinta (TAC) excede o limite configurado.",
                "A cobertura total de tinta (TAC) excede o limite de " + std::to_string(limit) +
                    "%. Isso pode causar problemas de secagem e borroes na impressao.",
                {{"max_tac_found", std::to_string(max_tac_found)},
                 {"tac_limit", std::to_string(limit)},
                 {"page_number", std::to_string(page_number)}}});
        } else if (max_tac_found > 0.9 * static_cast<double>(limit)) {
            findings.push_back({
                "PG_WARN_TAC_HIGH",
                "TacRule",
                "color",
                severity_from_rule(ctx.profile, "tac", domain::FindingSeverity::WARNING),
                domain::Fixability::NONE,
                page_number,
                "Cobertura total de tinta (TAC) proxima do limite configurado.",
                "A cobertura de tinta esta proxima do limite. Recomendamos verificar as areas com cores muito carregadas.",
                {{"max_tac_found", std::to_string(max_tac_found)},
                 {"tac_limit", std::to_string(limit)},
                 {"page_number", std::to_string(page_number)}}});
        }
    }

    return findings;
}

} // namespace printguard::analysis


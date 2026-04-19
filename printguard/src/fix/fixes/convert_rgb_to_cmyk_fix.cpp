#include "convert_rgb_to_cmyk_fix.hpp"

#include <iomanip>
#include <qpdf/Buffer.hh>
#include <qpdf/QPDF.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <regex>
#include <sstream>

namespace printguard::fix {

namespace {

struct CmykColor {
    double c = 0.0;
    double m = 0.0;
    double y = 0.0;
    double k = 0.0;
};

CmykColor rgb_to_cmyk(double r, double g, double b) {
    double k = 1.0 - std::max(r, std::max(g, b));
    if (k >= 0.999) {
        return {};
    }

    return {
        (1.0 - r - k) / (1.0 - k),
        (1.0 - g - k) / (1.0 - k),
        (1.0 - b - k) / (1.0 - k),
        k};
}

std::string format_color(const CmykColor& color, bool stroke) {
    std::ostringstream out;
    out << std::fixed << std::setprecision(4) << color.c << ' ' << color.m << ' ' << color.y << ' '
        << color.k << ' ' << (stroke ? 'K' : 'k');
    return out.str();
}

std::string replace_rgb_operators(const std::string& input, int& replacements) {
    std::regex pattern(
        R"(([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+(rg|RG))");
    std::string output;
    std::string::const_iterator current = input.begin();
    std::smatch match;

    while (std::regex_search(current, input.end(), match, pattern)) {
        output.append(current, match[0].first);

        double r = std::stod(match[1].str());
        double g = std::stod(match[2].str());
        double b = std::stod(match[3].str());
        bool neutral_gray = std::abs(r - g) < 0.001 && std::abs(g - b) < 0.001;

        if (neutral_gray) {
            output.append(match[0].str());
        } else {
            output.append(format_color(rgb_to_cmyk(r, g, b), match[4].str() == "RG"));
            ++replacements;
        }

        current = match[0].second;
    }

    output.append(current, input.end());
    return output;
}

std::string read_stream(QPDFObjectHandle stream) {
    auto data = stream.getStreamData(qpdf_dl_generalized);
    return std::string(reinterpret_cast<char const*>(data->getBuffer()), data->getSize());
}

} // namespace

std::string ConvertRgbToCmykFix::id() const {
    return "ConvertRgbToCmykFix";
}

std::string ConvertRgbToCmykFix::targets_finding_code() const {
    return "PG_ERR_RGB_COLORSPACE";
}

domain::FixRecord ConvertRgbToCmykFix::apply(FixContext& ctx) const {
    domain::FixRecord record;
    record.fix_id = id();
    record.finding_code = targets_finding_code();
    record.attempted = true;
    record.status = "applied";

    int replacements = 0;
    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();
    for (auto& page : pages) {
        for (auto& stream : page.getPageContents()) {
            std::string content = read_stream(stream);
            int stream_replacements = 0;
            std::string converted = replace_rgb_operators(content, stream_replacements);
            if (stream_replacements > 0) {
                stream.replaceStreamData(
                    converted, QPDFObjectHandle::newNull(), QPDFObjectHandle::newNull());
                replacements += stream_replacements;
            }
        }
    }

    record.success = replacements > 0;
    record.message = record.success ? "Operadores RGB diretos convertidos para CMYK."
                                    : "Nao havia operadores RGB conversiveis no conteudo.";
    record.details["operator_replacements"] = std::to_string(replacements);

    return record;
}

} // namespace printguard::fix

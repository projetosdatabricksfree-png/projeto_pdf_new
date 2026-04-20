#include "printguard/fix/fixes/spot_color_conversion_fix.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cctype>
#include <qpdf/Buffer.hh>
#include <qpdf/QPDFObjectHandle.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace printguard::fix {

namespace {

struct Token {
    std::string text;
    std::size_t start = 0;
    std::size_t end = 0;
};

struct Replacement {
    std::size_t start = 0;
    std::size_t end = 0;
    std::string replacement;
};

struct SpotSpec {
    int component_count = 0;
    std::array<double, 4> c0{};
    std::array<double, 4> c1{};
    double exponent = 1.0;
};

std::string read_stream(QPDFObjectHandle stream) {
    auto data = stream.getStreamData(qpdf_dl_generalized);
    return {reinterpret_cast<const char*>(data->getBuffer()), data->getSize()};
}

bool is_delim(char ch) {
    return std::isspace(static_cast<unsigned char>(ch)) || ch == '(' || ch == ')' || ch == '<' ||
        ch == '>' || ch == '[' || ch == ']' || ch == '{' || ch == '}' || ch == '/' || ch == '%';
}

std::vector<Token> tokenize_with_offsets(const std::string& content) {
    std::vector<Token> out;
    std::size_t i = 0;
    while (i < content.size()) {
        char ch = content[i];
        if (std::isspace(static_cast<unsigned char>(ch))) {
            ++i;
            continue;
        }
        if (ch == '%') {
            while (i < content.size() && content[i] != '\n' && content[i] != '\r') {
                ++i;
            }
            continue;
        }
        if (ch == '(') {
            ++i;
            int depth = 1;
            while (i < content.size() && depth > 0) {
                if (content[i] == '\\') {
                    i = std::min(content.size(), i + 2);
                    continue;
                }
                if (content[i] == '(') {
                    ++depth;
                } else if (content[i] == ')') {
                    --depth;
                }
                ++i;
            }
            continue;
        }
        if (ch == '<' && i + 1 < content.size() && content[i + 1] != '<') {
            ++i;
            while (i < content.size() && content[i] != '>') {
                ++i;
            }
            if (i < content.size()) {
                ++i;
            }
            continue;
        }

        std::size_t start = i;
        if (ch == '/') {
            ++i;
            while (i < content.size() && !is_delim(content[i])) {
                ++i;
            }
        } else {
            while (i < content.size() && !std::isspace(static_cast<unsigned char>(content[i])) &&
                   content[i] != '%') {
                ++i;
            }
        }
        out.push_back({content.substr(start, i - start), start, i});
    }
    return out;
}

std::string apply_replacements(
    const std::string& content,
    const std::vector<Replacement>& replacements) {
    if (replacements.empty()) {
        return content;
    }

    std::string output;
    std::size_t cursor = 0;
    for (const auto& item : replacements) {
        output.append(content.substr(cursor, item.start - cursor));
        output.append(item.replacement);
        cursor = item.end;
    }
    output.append(content.substr(cursor));
    return output;
}

bool array_to_cmyk(QPDFObjectHandle array, std::array<double, 4>& out) {
    if (!array.isArray() || array.getArrayNItems() != 4) {
        return false;
    }
    for (int index = 0; index < 4; ++index) {
        QPDFObjectHandle item = array.getArrayItem(index);
        if (!(item.isReal() || item.isInteger())) {
            return false;
        }
        out[static_cast<std::size_t>(index)] = item.getNumericValue();
    }
    return true;
}

bool read_type2_function(QPDFObjectHandle function, std::array<double, 4>& c0, std::array<double, 4>& c1, double& exponent) {
    if (!function.isDictionary()) {
        return false;
    }
    QPDFObjectHandle function_type = function.getKey("/FunctionType");
    if (!function_type.isInteger() || function_type.getIntValueAsInt() != 2) {
        return false;
    }
    if (!array_to_cmyk(function.getKey("/C0"), c0) || !array_to_cmyk(function.getKey("/C1"), c1)) {
        return false;
    }
    QPDFObjectHandle n = function.getKey("/N");
    if (!(n.isReal() || n.isInteger())) {
        return false;
    }
    exponent = n.getNumericValue();
    return true;
}

bool collect_simple_spots(
    QPDFObjectHandle color_spaces,
    std::unordered_map<std::string, SpotSpec>& convertible,
    int& skipped) {
    if (!color_spaces.isDictionary()) {
        return false;
    }

    bool found_any = false;
    for (const auto& key : color_spaces.getKeys()) {
        QPDFObjectHandle value = color_spaces.getKey(key);
        if (!value.isArray() || value.getArrayNItems() < 4) {
            continue;
        }

        QPDFObjectHandle kind = value.getArrayItem(0);
        if (!kind.isName()) {
            continue;
        }

        std::string kind_name = kind.getName();
        if (kind_name == "/Separation") {
            found_any = true;
            if (!value.getArrayItem(2).isName() || value.getArrayItem(2).getName() != "/DeviceCMYK") {
                ++skipped;
                continue;
            }
            SpotSpec spec;
            spec.component_count = 1;
            if (!read_type2_function(value.getArrayItem(3), spec.c0, spec.c1, spec.exponent)) {
                ++skipped;
                continue;
            }
            convertible.emplace(key, spec);
            continue;
        }

        if (kind_name == "/DeviceN") {
            found_any = true;
            if (value.getArrayNItems() < 4) {
                ++skipped;
                continue;
            }
            QPDFObjectHandle names = value.getArrayItem(1);
            QPDFObjectHandle alternate = value.getArrayItem(2);
            if (!names.isArray() || !alternate.isName() || alternate.getName() != "/DeviceCMYK") {
                ++skipped;
                continue;
            }
            if (names.getArrayNItems() != 4) {
                ++skipped;
                continue;
            }

            // MVP simple case: DeviceN already carrying four tint components and alternate CMYK.
            SpotSpec spec;
            spec.component_count = 4;
            convertible.emplace(key, spec);
        }
    }
    return found_any;
}

std::string format_cmyk(const std::array<double, 4>& cmyk, bool stroke) {
    std::ostringstream out;
    out.setf(std::ios::fixed, std::ios::floatfield);
    out.precision(4);
    out << cmyk[0] << ' ' << cmyk[1] << ' ' << cmyk[2] << ' ' << cmyk[3] << ' '
        << (stroke ? 'K' : 'k');
    return out.str();
}

std::array<double, 4> evaluate_spot(const SpotSpec& spec, const std::vector<double>& tints) {
    if (spec.component_count == 4) {
        return {tints[0], tints[1], tints[2], tints[3]};
    }

    double tint = std::clamp(tints.front(), 0.0, 1.0);
    double power = std::pow(tint, spec.exponent);
    std::array<double, 4> out{};
    for (std::size_t index = 0; index < out.size(); ++index) {
        out[index] = spec.c0[index] + power * (spec.c1[index] - spec.c0[index]);
        out[index] = std::clamp(out[index], 0.0, 1.0);
    }
    return out;
}

bool parse_number(const std::string& token, double& value) {
    if (token.empty()) {
        return false;
    }
    if (!(std::isdigit(static_cast<unsigned char>(token[0])) || token[0] == '-' || token[0] == '+' ||
          token[0] == '.')) {
        return false;
    }
    try {
        value = std::stod(token);
        return true;
    } catch (...) {
        return false;
    }
}

int rewrite_spot_usage(
    QPDFObjectHandle stream,
    const std::unordered_map<std::string, SpotSpec>& specs) {
    if (specs.empty()) {
        return 0;
    }

    std::string content = read_stream(stream);
    std::vector<Token> tokens = tokenize_with_offsets(content);
    std::vector<Replacement> replacements;
    std::string current_fill_space = "/DeviceGray";
    std::string current_stroke_space = "/DeviceGray";
    int converted = 0;

    for (std::size_t i = 0; i < tokens.size(); ++i) {
        const auto& token = tokens[i];
        if (token.text == "cs" && i >= 1) {
            current_fill_space = tokens[i - 1].text;
            continue;
        }
        if (token.text == "CS" && i >= 1) {
            current_stroke_space = tokens[i - 1].text;
            continue;
        }
        if ((token.text == "scn" || token.text == "SCN")) {
            bool stroke = token.text == "SCN";
            const std::string& active_space = stroke ? current_stroke_space : current_fill_space;
            auto it = specs.find(active_space);
            if (it == specs.end()) {
                continue;
            }

            const SpotSpec& spec = it->second;
            if (i < static_cast<std::size_t>(spec.component_count)) {
                continue;
            }

            std::vector<double> tints;
            tints.reserve(static_cast<std::size_t>(spec.component_count));
            bool valid = true;
            for (int component = spec.component_count; component > 0; --component) {
                double value = 0.0;
                if (!parse_number(tokens[i - static_cast<std::size_t>(component)].text, value)) {
                    valid = false;
                    break;
                }
                tints.push_back(std::clamp(value, 0.0, 1.0));
            }
            if (!valid) {
                continue;
            }

            std::array<double, 4> cmyk = evaluate_spot(spec, tints);
            replacements.push_back(
                {tokens[i - static_cast<std::size_t>(spec.component_count)].start,
                 token.end,
                 format_cmyk(cmyk, stroke)});
            ++converted;
        }
    }

    if (converted > 0) {
        stream.replaceStreamData(
            apply_replacements(content, replacements),
            QPDFObjectHandle::newNull(),
            QPDFObjectHandle::newNull());
    }

    return converted;
}

} // namespace

std::string SpotColorConversionFix::id() const {
    return "SpotColorConversionFix";
}

std::string SpotColorConversionFix::targets_finding_code() const {
    return "PG_WARN_SPOT_COLORS";
}

domain::FixRecord SpotColorConversionFix::apply(FixContext& ctx) const {
    domain::FixRecord record;
    record.fix_id = id();
    record.finding_code = targets_finding_code();
    record.attempted = true;
    record.status = "applied";

    int spots_converted = 0;
    int spots_skipped = 0;

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();
    for (auto& page : pages) {
        QPDFObjectHandle resources = page.getAttribute("/Resources", true);
        QPDFObjectHandle color_spaces = resources.getKey("/ColorSpace");

        std::unordered_map<std::string, SpotSpec> specs;
        bool found_spot = collect_simple_spots(color_spaces, specs, spots_skipped);
        if (!found_spot) {
            continue;
        }

        for (const auto& [key, spec] : specs) {
            color_spaces.replaceKey(key, QPDFObjectHandle::newName("/DeviceCMYK"));
            ++spots_converted;
            (void)spec;
        }

        page.coalesceContentStreams();
        auto streams = page.getPageContents();
        if (!streams.empty()) {
            rewrite_spot_usage(streams.front(), specs);
        }
    }

    record.success = spots_converted > 0;
    record.message = record.success
        ? "Cores especiais (spot/Pantone) foram convertidas para CMYK."
        : "Nenhuma spot color simples e segura foi convertida para CMYK.";
    record.details["spots_converted"] = std::to_string(spots_converted);
    record.details["spots_skipped"] = std::to_string(spots_skipped);

    return record;
}

} // namespace printguard::fix

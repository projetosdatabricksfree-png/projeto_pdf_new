#include "printguard/fix/fixes/black_normalization_fix.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <qpdf/Buffer.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <set>
#include <sstream>
#include <string>
#include <vector>

namespace printguard::fix {

namespace {

struct Token {
    std::string text;
    std::size_t start = 0;
    std::size_t end = 0;
    bool is_number = false;
    double number_value = 0.0;
};

struct Replacement {
    std::size_t start = 0;
    std::size_t end = 0;
    std::string text;
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
        if (ch == '/') {
            std::size_t start = i;
            ++i;
            while (i < content.size() && !is_delim(content[i])) {
                ++i;
            }
            out.push_back({content.substr(start, i - start), start, i, false, 0.0});
            continue;
        }

        std::size_t start = i;
        while (i < content.size() && !std::isspace(static_cast<unsigned char>(content[i])) &&
               content[i] != '%') {
            ++i;
        }
        std::string text = content.substr(start, i - start);
        try {
            out.push_back({text, start, i, true, std::stod(text)});
        } catch (...) {
            out.push_back({text, start, i, false, 0.0});
        }
    }
    return out;
}

bool nearly_equal(double a, double b) {
    return std::abs(a - b) < 0.001;
}

bool is_rich_black(double c, double m, double y, double k) {
    bool has_cmy = (c > 0.001) || (m > 0.001) || (y > 0.001);
    bool k_is_full = k > 0.9 || nearly_equal(k, 1.0);
    return has_cmy && k_is_full;
}

std::string apply_replacements(
    const std::string& content,
    const std::vector<Replacement>& replacements) {
    if (replacements.empty()) {
        return content;
    }

    std::string output;
    std::size_t cursor = 0;
    for (const auto& replacement : replacements) {
        output.append(content.substr(cursor, replacement.start - cursor));
        output.append(replacement.text);
        cursor = replacement.end;
    }
    output.append(content.substr(cursor));
    return output;
}

std::string normalize_rich_black_text(
    const std::string& content,
    int& replacements_count) {
    std::vector<Token> tokens = tokenize_with_offsets(content);
    std::vector<Replacement> replacements;
    std::vector<Token> number_stack;
    bool in_text = false;

    auto clear_stack = [&]() { number_stack.clear(); };

    for (const auto& token : tokens) {
        if (token.text == "BT") {
            in_text = true;
            clear_stack();
            continue;
        }
        if (token.text == "ET") {
            in_text = false;
            clear_stack();
            continue;
        }

        if (token.is_number) {
            number_stack.push_back(token);
            continue;
        }

        if (in_text && (token.text == "k" || token.text == "K") && number_stack.size() >= 4) {
            const Token& c = number_stack[number_stack.size() - 4];
            const Token& m = number_stack[number_stack.size() - 3];
            const Token& y = number_stack[number_stack.size() - 2];
            const Token& k = number_stack[number_stack.size() - 1];
            if (is_rich_black(c.number_value, m.number_value, y.number_value, k.number_value)) {
                replacements.push_back(
                    {c.start, token.end, "0 0 0 1 " + token.text});
                ++replacements_count;
            }
            clear_stack();
            continue;
        }

        clear_stack();
    }

    return apply_replacements(content, replacements);
}

} // namespace

std::string BlackNormalizationFix::id() const {
    return "BlackNormalizationFix";
}

std::string BlackNormalizationFix::targets_finding_code() const {
    return "PG_WARN_RICH_BLACK_TEXT";
}

domain::FixRecord BlackNormalizationFix::apply(FixContext& ctx) const {
    domain::FixRecord record;
    record.fix_id = id();
    record.finding_code = targets_finding_code();
    record.attempted = true;
    record.status = "applied";

    int replacements_count = 0;
    std::set<int> pages_affected;

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();
    for (std::size_t page_index = 0; page_index < pages.size(); ++page_index) {
        auto& page = pages.at(page_index);
        page.coalesceContentStreams();
        auto streams = page.getPageContents();
        if (streams.empty()) {
            continue;
        }

        auto stream = streams.front();
        std::string content = read_stream(stream);
        int page_replacements = 0;
        std::string normalized = normalize_rich_black_text(content, page_replacements);
        if (page_replacements > 0) {
            stream.replaceStreamData(
                normalized, QPDFObjectHandle::newNull(), QPDFObjectHandle::newNull());
            replacements_count += page_replacements;
            pages_affected.insert(static_cast<int>(page_index + 1));
        }
    }

    record.success = replacements_count > 0;
    record.message = record.success
        ? "Texto com preto composto foi normalizado para preto puro (100% K) para melhor qualidade de impressao."
        : "Nao havia preto composto em blocos de texto para normalizar.";
    record.details["replacements_count"] = std::to_string(replacements_count);
    record.details["pages_affected"] = std::to_string(pages_affected.size());

    return record;
}

} // namespace printguard::fix

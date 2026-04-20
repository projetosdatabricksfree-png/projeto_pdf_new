#include "black_consistency_rule.hpp"

#include <cctype>
#include <cmath>
#include <qpdf/Buffer.hh>
#include <qpdf/QPDF.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <sstream>
#include <string>
#include <vector>

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

bool is_delim(char ch) {
    return std::isspace(static_cast<unsigned char>(ch)) || ch == '(' || ch == ')' || ch == '<' ||
        ch == '>' || ch == '[' || ch == ']' || ch == '{' || ch == '}' || ch == '/' || ch == '%';
}

std::vector<std::string> tokenize(std::string const& content) {
    std::vector<std::string> out;
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
                    i += 2;
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
        if (ch == '<') {
            if (i + 1 < content.size() && content[i + 1] != '<') {
                ++i;
                while (i < content.size() && content[i] != '>') {
                    ++i;
                }
                if (i < content.size()) {
                    ++i;
                }
                continue;
            }
        }
        if (ch == '/') {
            std::size_t start = i;
            ++i;
            while (i < content.size() && !is_delim(content[i])) {
                ++i;
            }
            out.push_back(content.substr(start, i - start));
            continue;
        }

        std::size_t start = i;
        while (i < content.size() && !std::isspace(static_cast<unsigned char>(content[i]))) {
            if (content[i] == '%') {
                break;
            }
            ++i;
        }
        out.push_back(content.substr(start, i - start));
    }
    return out;
}

struct Operand {
    enum class Kind { number, name, other };
    Kind kind = Kind::other;
    double number_value = 0.0;
    std::string text;
};

bool nearly_equal(double a, double b) {
    return std::abs(a - b) < 0.001;
}

bool is_rich_black(double c, double m, double y, double k) {
    bool has_cmy = (c > 0.001) || (m > 0.001) || (y > 0.001);
    bool k_is_full = k > 0.99 || nearly_equal(k, 1.0);
    return has_cmy && k_is_full;
}

std::string format_sample(double c, double m, double y, double k) {
    std::ostringstream out;
    out << c << ' ' << m << ' ' << y << ' ' << k;
    return out.str();
}

} // namespace

std::string BlackConsistencyRule::id() const {
    return "black_consistency";
}

std::string BlackConsistencyRule::category() const {
    return "color";
}

std::vector<domain::Finding> BlackConsistencyRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    if (!ctx.preset.text_policy.normalize_rich_black_small_text) {
        return findings;
    }

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();

    for (std::size_t page_index = 0; page_index < pages.size(); ++page_index) {
        auto& page = pages.at(page_index);

        bool in_text = false;
        int rich_black_count = 0;
        std::vector<std::string> samples;

        std::vector<std::string> tokens = tokenize(read_page_content(page));
        std::vector<Operand> stack;

        auto clear_stack = [&]() { stack.clear(); };
        auto pop_number = [&]() -> double {
            double v = 0.0;
            if (!stack.empty() && stack.back().kind == Operand::Kind::number) {
                v = stack.back().number_value;
            }
            if (!stack.empty()) {
                stack.pop_back();
            }
            return v;
        };

        for (auto const& t : tokens) {
            if (!t.empty() && (std::isdigit(static_cast<unsigned char>(t[0])) || t[0] == '-' || t[0] == '+' || t[0] == '.')) {
                try {
                    stack.push_back({Operand::Kind::number, std::stod(t), {}});
                } catch (...) {
                    stack.push_back({Operand::Kind::other, 0.0, t});
                }
                continue;
            }
            if (!t.empty() && t[0] == '/') {
                stack.push_back({Operand::Kind::name, 0.0, t});
                continue;
            }

            if (t == "BT") {
                in_text = true;
                clear_stack();
                continue;
            }
            if (t == "ET") {
                in_text = false;
                clear_stack();
                continue;
            }

            if (t == "k") {
                double kk = pop_number();
                double yy = pop_number();
                double mm = pop_number();
                double cc = pop_number();
                if (in_text && is_rich_black(cc, mm, yy, kk)) {
                    ++rich_black_count;
                    if (samples.size() < 3) {
                        samples.push_back(format_sample(cc, mm, yy, kk));
                    }
                }
                clear_stack();
                continue;
            }

            clear_stack();
        }

        if (rich_black_count > 0) {
            int page_number = static_cast<int>(page_index + 1);
            std::string sample_values;
            for (std::size_t i = 0; i < samples.size(); ++i) {
                if (i > 0) {
                    sample_values += "; ";
                }
                sample_values += samples[i];
            }

            findings.push_back({
                "PG_WARN_RICH_BLACK_TEXT",
                "BlackConsistencyRule",
                "color",
                severity_from_rule(ctx.profile, "black_consistency", domain::FindingSeverity::WARNING),
                domain::Fixability::AUTOMATIC_SAFE,
                page_number,
                "Texto com preto composto (rico) detectado em content streams.",
                "Texto com preto composto (rico) detectado. Textos pequenos com preto rico podem ter problemas de registro na impressao.",
                {{"rich_black_count", std::to_string(rich_black_count)},
                 {"page_number", std::to_string(page_number)},
                 {"sample_values", sample_values}}});
        }
    }

    return findings;
}

} // namespace printguard::analysis


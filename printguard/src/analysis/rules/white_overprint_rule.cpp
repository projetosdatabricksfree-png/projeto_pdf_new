#include "white_overprint_rule.hpp"

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

struct Operand {
    enum class Kind { number, name, other };
    Kind kind = Kind::other;
    double number_value = 0.0;
    std::string text;
};

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
            // hex string or dict start; skip hex string <...>
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

bool nearly_equal(double a, double b) {
    return std::abs(a - b) < 0.001;
}

bool is_white_cmyk(double c, double m, double y, double k) {
    return nearly_equal(c, 0.0) && nearly_equal(m, 0.0) && nearly_equal(y, 0.0) && nearly_equal(k, 0.0);
}

bool is_white_rgb(double r, double g, double b) {
    return nearly_equal(r, 1.0) && nearly_equal(g, 1.0) && nearly_equal(b, 1.0);
}

bool is_white_gray(double g) {
    return nearly_equal(g, 1.0);
}

struct OverprintState {
    bool stroke = false;
    bool fill = false;
};

OverprintState apply_extgstate(OverprintState state, QPDFObjectHandle ext_gstate) {
    if (!ext_gstate.isDictionary()) {
        return state;
    }
    if (ext_gstate.hasKey("/OP")) {
        state.stroke = ext_gstate.getKey("/OP").getBoolValue();
    }
    if (ext_gstate.hasKey("/op")) {
        state.fill = ext_gstate.getKey("/op").getBoolValue();
    }
    return state;
}

} // namespace

std::string WhiteOverprintRule::id() const {
    return "white_overprint";
}

std::string WhiteOverprintRule::category() const {
    return "print_risk";
}

std::vector<domain::Finding> WhiteOverprintRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    if (!ctx.preset.text_policy.forbid_white_overprint) {
        return findings;
    }

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();

    for (std::size_t page_index = 0; page_index < pages.size(); ++page_index) {
        auto& page = pages.at(page_index);
        QPDFObjectHandle resources = page.getAttribute("/Resources", false);
        QPDFObjectHandle ext_gstate_dict = resources.getKey("/ExtGState");

        OverprintState op_state{};
        bool fill_is_white = false;
        bool stroke_is_white = false;

        bool violation = false;

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
        auto pop_name = [&]() -> std::string {
            std::string v;
            if (!stack.empty() && stack.back().kind == Operand::Kind::name) {
                v = stack.back().text;
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

            // operator
            if (t == "gs") {
                std::string name = pop_name();
                if (ext_gstate_dict.isDictionary() && !name.empty()) {
                    QPDFObjectHandle state = ext_gstate_dict.getKey(name);
                    op_state = apply_extgstate(op_state, state);
                }
                clear_stack();
            } else if (t == "k") {
                double kk = pop_number();
                double yy = pop_number();
                double mm = pop_number();
                double cc = pop_number();
                fill_is_white = is_white_cmyk(cc, mm, yy, kk);
                if (op_state.fill && fill_is_white) {
                    violation = true;
                }
                clear_stack();
            } else if (t == "K") {
                double kk = pop_number();
                double yy = pop_number();
                double mm = pop_number();
                double cc = pop_number();
                stroke_is_white = is_white_cmyk(cc, mm, yy, kk);
                if (op_state.stroke && stroke_is_white) {
                    violation = true;
                }
                clear_stack();
            } else if (t == "rg") {
                double b = pop_number();
                double g = pop_number();
                double r = pop_number();
                fill_is_white = is_white_rgb(r, g, b);
                if (op_state.fill && fill_is_white) {
                    violation = true;
                }
                clear_stack();
            } else if (t == "RG") {
                double b = pop_number();
                double g = pop_number();
                double r = pop_number();
                stroke_is_white = is_white_rgb(r, g, b);
                if (op_state.stroke && stroke_is_white) {
                    violation = true;
                }
                clear_stack();
            } else if (t == "g") {
                double gray = pop_number();
                fill_is_white = is_white_gray(gray);
                if (op_state.fill && fill_is_white) {
                    violation = true;
                }
                clear_stack();
            } else if (t == "G") {
                double gray = pop_number();
                stroke_is_white = is_white_gray(gray);
                if (op_state.stroke && stroke_is_white) {
                    violation = true;
                }
                clear_stack();
            } else {
                clear_stack();
            }

            if (violation) {
                break;
            }
        }

        if (violation) {
            int page_number = static_cast<int>(page_index + 1);
            findings.push_back({
                "PG_ERR_WHITE_OVERPRINT",
                "WhiteOverprintRule",
                "print_risk",
                severity_from_rule(ctx.profile, "white_overprint", domain::FindingSeverity::ERROR),
                domain::Fixability::AUTOMATIC_SAFE,
                page_number,
                "Overprint ativado em contexto de cor branca.",
                "Detectado texto ou objeto branco com overprint ativado. Isso faz o branco ficar invisivel na impressao.",
                {{"page_number", std::to_string(page_number)}}});
        }
    }

    return findings;
}

} // namespace printguard::analysis


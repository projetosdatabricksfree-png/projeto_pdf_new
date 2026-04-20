#include "printguard/fix/fixes/flatten_layers_fix.hpp"

#include <cctype>
#include <qpdf/Buffer.hh>
#include <qpdf/QPDFObjectHandle.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <string>
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

int remove_layer_markers_from_page(QPDFObjectHandle stream) {
    std::string content = read_stream(stream);
    std::vector<Token> tokens = tokenize_with_offsets(content);
    std::vector<Replacement> replacements;
    int removed = 0;

    for (std::size_t i = 0; i < tokens.size(); ++i) {
        if (tokens[i].text == "BDC" && i >= 2 && tokens[i - 2].text == "/OC" &&
            !tokens[i - 1].text.empty() && tokens[i - 1].text.front() == '/') {
            replacements.push_back({tokens[i - 2].start, tokens[i].end, ""});
            ++removed;
            continue;
        }
        if (tokens[i].text == "EMC") {
            replacements.push_back({tokens[i].start, tokens[i].end, ""});
            ++removed;
        }
    }

    if (removed > 0) {
        stream.replaceStreamData(
            apply_replacements(content, replacements),
            QPDFObjectHandle::newNull(),
            QPDFObjectHandle::newNull());
    }

    return removed;
}

} // namespace

std::string FlattenLayersFix::id() const {
    return "FlattenLayersFix";
}

std::string FlattenLayersFix::targets_finding_code() const {
    return "PG_WARN_LAYERS_PRESENT";
}

domain::FixRecord FlattenLayersFix::apply(FixContext& ctx) const {
    domain::FixRecord record;
    record.fix_id = id();
    record.finding_code = targets_finding_code();
    record.attempted = true;
    record.status = "applied";

    int flattened = 0;
    QPDFObjectHandle root = ctx.pdf.getRoot();
    if (root.hasKey("/OCProperties")) {
        root.removeKey("/OCProperties");
        ++flattened;
    }

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();
    for (auto& page : pages) {
        QPDFObjectHandle resources = page.getAttribute("/Resources", true);
        QPDFObjectHandle properties = resources.getKey("/Properties");
        if (properties.isDictionary()) {
            std::vector<std::string> keys_to_remove;
            for (const auto& key : properties.getKeys()) {
                QPDFObjectHandle value = properties.getKey(key);
                if (!value.isDictionary()) {
                    continue;
                }
                QPDFObjectHandle type = value.getKey("/Type");
                if (type.isName() && (type.getName() == "/OCG" || type.getName() == "/OCMD")) {
                    keys_to_remove.push_back(key);
                }
            }
            for (const auto& key : keys_to_remove) {
                properties.removeKey(key);
                ++flattened;
            }
            if (properties.getKeys().empty()) {
                resources.removeKey("/Properties");
            }
        }

        page.coalesceContentStreams();
        auto streams = page.getPageContents();
        if (!streams.empty()) {
            flattened += remove_layer_markers_from_page(streams.front());
        }
    }

    record.success = flattened > 0;
    record.message = record.success
        ? "Camadas (layers) foram removidas. Todo o conteudo visivel foi preservado."
        : "Nao havia metadados de layer para remover.";
    record.details["layers_flattened"] = std::to_string(flattened);

    return record;
}

} // namespace printguard::fix

#include "annotation_rule.hpp"

#include <qpdf/QPDF.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <set>
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

std::string clean_pdf_name(std::string value) {
    if (!value.empty() && value.front() == '/') {
        value.erase(value.begin());
    }
    return value;
}

std::string join_names(const std::set<std::string>& values) {
    std::ostringstream out;
    bool first = true;
    for (auto const& value : values) {
        if (!first) {
            out << ", ";
        }
        out << value;
        first = false;
    }
    return out.str();
}

} // namespace

std::string AnnotationRule::id() const {
    return "annotations";
}

std::string AnnotationRule::category() const {
    return "structure";
}

std::vector<domain::Finding> AnnotationRule::evaluate(const RuleContext& ctx) const {
    std::vector<domain::Finding> findings;

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();

    for (std::size_t index = 0; index < pages.size(); ++index) {
        auto& page = pages.at(index);
        QPDFObjectHandle annots = page.getAttribute("/Annots", false);
        if (!annots.isArray()) {
            continue;
        }

        int annotation_count = 0;
        std::set<std::string> annotation_types;
        for (int annotation_index = 0; annotation_index < annots.getArrayNItems(); ++annotation_index) {
            QPDFObjectHandle annot = annots.getArrayItem(annotation_index);
            if (!annot.isDictionary()) {
                continue;
            }

            QPDFObjectHandle subtype = annot.getKey("/Subtype");
            if (!subtype.isName()) {
                continue;
            }

            std::string subtype_name = clean_pdf_name(subtype.getName());
            if (subtype_name == "Link") {
                continue;
            }

            ++annotation_count;
            annotation_types.insert(subtype_name);
        }

        if (annotation_count == 0) {
            continue;
        }

        int page_number = static_cast<int>(index + 1);
        findings.push_back({
            "PG_WARN_ANNOTATIONS",
            "AnnotationRule",
            "structure",
            severity_from_rule(ctx.profile, "annotations", domain::FindingSeverity::WARNING),
            domain::Fixability::AUTOMATIC_SAFE,
            page_number,
            "Pagina contem anotacoes nao-link no array /Annots.",
            "Detectadas anotacoes/comentarios no arquivo. Esses elementos nao sao impressos e serao removidos.",
            {{"annotation_count", std::to_string(annotation_count)},
             {"annotation_types", join_names(annotation_types)},
             {"page_number", std::to_string(page_number)}}});
    }

    return findings;
}

} // namespace printguard::analysis

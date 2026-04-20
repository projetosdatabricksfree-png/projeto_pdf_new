#include "printguard/fix/fixes/remove_white_overprint_fix.hpp"

#include <qpdf/QPDFObjectHandle.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <set>

namespace printguard::fix {

namespace {

std::set<int> target_pages(const FixContext& ctx, const std::string& finding_code) {
    std::set<int> pages;
    for (const auto& finding : ctx.findings) {
        if (finding.code == finding_code && finding.page_number > 0) {
            pages.insert(finding.page_number);
        }
    }
    return pages;
}

} // namespace

std::string RemoveWhiteOverprintFix::id() const {
    return "RemoveWhiteOverprintFix";
}

std::string RemoveWhiteOverprintFix::targets_finding_code() const {
    return "PG_ERR_WHITE_OVERPRINT";
}

domain::FixRecord RemoveWhiteOverprintFix::apply(FixContext& ctx) const {
    domain::FixRecord record;
    record.fix_id = id();
    record.finding_code = targets_finding_code();
    record.attempted = true;
    record.status = "applied";

    std::set<int> pages_to_fix = target_pages(ctx, targets_finding_code());
    int entries_removed = 0;

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();
    for (std::size_t index = 0; index < pages.size(); ++index) {
        int page_number = static_cast<int>(index + 1);
        if (!pages_to_fix.empty() && !pages_to_fix.contains(page_number)) {
            continue;
        }

        auto& page = pages.at(index);
        QPDFObjectHandle resources = page.getAttribute("/Resources", true);
        QPDFObjectHandle ext_gstate = resources.getKey("/ExtGState");
        if (!ext_gstate.isDictionary()) {
            continue;
        }

        for (const auto& key : ext_gstate.getKeys()) {
            QPDFObjectHandle state = ext_gstate.getKey(key);
            if (!state.isDictionary()) {
                continue;
            }
            bool touched = false;
            if (state.hasKey("/OP") && state.getKey("/OP").getBoolValue()) {
                state.replaceKey("/OP", QPDFObjectHandle::newBool(false));
                touched = true;
            }
            if (state.hasKey("/op") && state.getKey("/op").getBoolValue()) {
                state.replaceKey("/op", QPDFObjectHandle::newBool(false));
                touched = true;
            }
            if (touched) {
                ++entries_removed;
            }
        }
    }

    record.success = entries_removed > 0;
    record.message = record.success
        ? "Overprint em objetos brancos foi removido para evitar desaparecimento na impressao."
        : "Nao havia entradas de overprint branco para ajustar.";
    record.details["overprint_entries_removed"] = std::to_string(entries_removed);

    return record;
}

} // namespace printguard::fix

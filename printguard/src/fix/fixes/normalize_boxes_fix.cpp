#include "normalize_boxes_fix.hpp"

#include <qpdf/QPDF.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>

namespace printguard::fix {

std::string NormalizeBoxesFix::id() const {
    return "NormalizeBoxesFix";
}

std::string NormalizeBoxesFix::targets_finding_code() const {
    return "PG_ERR_MISSING_BLEED_BOX";
}

domain::FixRecord NormalizeBoxesFix::apply(FixContext& ctx) const {
    domain::FixRecord record;
    record.fix_id = id();
    record.finding_code = targets_finding_code();
    record.attempted = true;
    record.status = "applied";

    int pages_updated = 0;
    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();
    for (auto& page : pages) {
        QPDFObjectHandle page_object = page.getObjectHandle();
        if (page_object.hasKey("/BleedBox")) {
            continue;
        }

        page_object.replaceKey("/BleedBox", page.getMediaBox(true));
        ++pages_updated;
    }

    record.success = pages_updated > 0;
    record.message = record.success ? "BleedBox explicita criada a partir da MediaBox."
                                    : "Nenhuma pagina exigiu normalizacao de BleedBox.";
    record.details["pages_updated"] = std::to_string(pages_updated);

    return record;
}

} // namespace printguard::fix

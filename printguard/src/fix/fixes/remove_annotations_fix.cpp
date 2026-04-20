#include "printguard/fix/fixes/remove_annotations_fix.hpp"

#include <qpdf/QPDFObjectHandle.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>

namespace printguard::fix {

std::string RemoveAnnotationsFix::id() const {
    return "RemoveAnnotationsFix";
}

std::string RemoveAnnotationsFix::targets_finding_code() const {
    return "PG_WARN_ANNOTATIONS";
}

domain::FixRecord RemoveAnnotationsFix::apply(FixContext& ctx) const {
    domain::FixRecord record;
    record.fix_id = id();
    record.finding_code = targets_finding_code();
    record.attempted = true;
    record.status = "applied";

    int annotations_removed = 0;
    int annotations_preserved = 0;

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();
    for (auto& page : pages) {
        QPDFObjectHandle page_object = page.getObjectHandle();
        QPDFObjectHandle annots = page_object.getKey("/Annots");
        if (!annots.isArray()) {
            continue;
        }

        QPDFObjectHandle preserved = QPDFObjectHandle::newArray();
        for (int annotation_index = 0; annotation_index < annots.getArrayNItems(); ++annotation_index) {
            QPDFObjectHandle annot = annots.getArrayItem(annotation_index);
            if (!annot.isDictionary()) {
                ++annotations_removed;
                continue;
            }

            QPDFObjectHandle subtype = annot.getKey("/Subtype");
            if (subtype.isName() && subtype.getName() == "/Link") {
                preserved.appendItem(annot);
                ++annotations_preserved;
            } else {
                ++annotations_removed;
            }
        }

        if (preserved.getArrayNItems() == 0) {
            page_object.removeKey("/Annots");
        } else {
            page_object.replaceKey("/Annots", preserved);
        }
    }

    record.success = annotations_removed > 0;
    record.message = record.success
        ? "Comentarios e anotacoes nao imprimiveis foram removidos do arquivo."
        : "Nao havia anotacoes nao-link para remover.";
    record.details["annotations_removed"] = std::to_string(annotations_removed);
    record.details["annotations_preserved"] = std::to_string(annotations_preserved);

    return record;
}

} // namespace printguard::fix

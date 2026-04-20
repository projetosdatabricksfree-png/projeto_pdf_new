#include "printguard/fix/fixes/rotation_fix.hpp"

#include <algorithm>
#include <qpdf/QPDFObjectHandle.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>

namespace printguard::fix {

namespace {

int normalize_rotation(int rotation) {
    int normalized = rotation % 360;
    if (normalized < 0) {
        normalized += 360;
    }
    return normalized;
}

std::string page_orientation(QPDFPageObjectHelper& page) {
    QPDFObjectHandle trim_box = page.getTrimBox(false, false);
    QPDFObjectHandle media_box = page.getMediaBox(false);
    QPDFObjectHandle box = trim_box.isArray() ? trim_box : media_box;

    double left = box.getArrayItem(0).getNumericValue();
    double bottom = box.getArrayItem(1).getNumericValue();
    double right = box.getArrayItem(2).getNumericValue();
    double top = box.getArrayItem(3).getNumericValue();
    double width = std::abs(right - left);
    double height = std::abs(top - bottom);

    bool landscape = width > height;
    int rotation = normalize_rotation(page.getAttribute("/Rotate", false).getIntValueAsInt());
    if (rotation == 90 || rotation == 270) {
        landscape = !landscape;
    }

    return landscape ? "landscape" : "portrait";
}

bool base_is_landscape(QPDFPageObjectHelper& page) {
    QPDFObjectHandle trim_box = page.getTrimBox(false, false);
    QPDFObjectHandle media_box = page.getMediaBox(false);
    QPDFObjectHandle box = trim_box.isArray() ? trim_box : media_box;

    double left = box.getArrayItem(0).getNumericValue();
    double bottom = box.getArrayItem(1).getNumericValue();
    double right = box.getArrayItem(2).getNumericValue();
    double top = box.getArrayItem(3).getNumericValue();
    return std::abs(right - left) > std::abs(top - bottom);
}

} // namespace

std::string RotationFix::id() const {
    return "RotationFix";
}

std::string RotationFix::targets_finding_code() const {
    return "PG_WARN_ROTATION_MISMATCH";
}

domain::FixRecord RotationFix::apply(FixContext& ctx) const {
    domain::FixRecord record;
    record.fix_id = id();
    record.finding_code = targets_finding_code();
    record.attempted = true;
    record.status = "applied";

    if (ctx.preset.orientation == "either" ||
        (ctx.preset.orientation != "portrait" && ctx.preset.orientation != "landscape")) {
        record.success = false;
        record.message = "Orientacao ambigua; nenhuma pagina foi rotacionada.";
        record.details["pages_rotated"] = "0";
        return record;
    }

    int pages_rotated = 0;
    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();
    for (auto& page : pages) {
        if (page_orientation(page) == ctx.preset.orientation) {
            continue;
        }

        bool base_landscape = base_is_landscape(page);
        int desired_rotation = ((ctx.preset.orientation == "landscape") == base_landscape) ? 0 : 90;
        page.getObjectHandle().replaceKey("/Rotate", QPDFObjectHandle::newInteger(desired_rotation));
        ++pages_rotated;
    }

    record.success = pages_rotated > 0;
    record.message = record.success
        ? "Orientacao da pagina foi ajustada para corresponder ao produto."
        : "Nenhuma pagina precisou de ajuste de /Rotate.";
    record.details["pages_rotated"] = std::to_string(pages_rotated);

    return record;
}

} // namespace printguard::fix

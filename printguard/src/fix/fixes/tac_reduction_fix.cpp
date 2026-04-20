#include "printguard/fix/fixes/tac_reduction_fix.hpp"

#include "../pdf_color_utils.hpp"

#include <algorithm>
#include <cmath>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <set>

namespace printguard::fix {

namespace {

double byte_to_unit(unsigned char value) {
    return static_cast<double>(value) / 255.0;
}

unsigned char unit_to_byte(double value) {
    double clamped = std::clamp(value, 0.0, 1.0);
    return static_cast<unsigned char>(std::lround(clamped * 255.0));
}

double pixel_tac_percent(
    unsigned char c,
    unsigned char m,
    unsigned char y,
    unsigned char k) {
    return (byte_to_unit(c) + byte_to_unit(m) + byte_to_unit(y) + byte_to_unit(k)) * 100.0;
}

} // namespace

std::string TacReductionFix::id() const {
    return "TacReductionFix";
}

std::string TacReductionFix::targets_finding_code() const {
    return "PG_ERR_TAC_EXCEEDED";
}

domain::FixRecord TacReductionFix::apply(FixContext& ctx) const {
    domain::FixRecord record;
    record.fix_id = id();
    record.finding_code = targets_finding_code();
    record.attempted = true;
    record.status = "applied";

    const double max_tac = static_cast<double>(ctx.preset.max_total_ink_percent);
    const double max_tac_unit = max_tac / 100.0;
    std::size_t pixels_modified = 0;
    double max_tac_before = 0.0;
    double max_tac_after = 0.0;
    std::set<int> pages_affected;

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();
    for (std::size_t page_index = 0; page_index < pages.size(); ++page_index) {
        auto& page = pages.at(page_index);
        bool page_changed = false;

        for (auto& [name, image] : page.getImages()) {
            (void)name;
            if (!image.isStream()) {
                continue;
            }

            QPDFObjectHandle dict = image.getDict();
            QPDFObjectHandle subtype = dict.getKey("/Subtype");
            if (!subtype.isName() || subtype.getName() != "/Image") {
                continue;
            }

            QPDFObjectHandle color_space = resolve_image_colorspace(page, dict);
            if (!is_device_cmyk_colorspace(color_space)) {
                continue;
            }

            int width = get_integer(dict, "/Width");
            int height = get_integer(dict, "/Height");
            int bits_per_component = get_integer(dict, "/BitsPerComponent");
            if (width <= 0 || height <= 0 || bits_per_component != 8) {
                continue;
            }

            std::vector<unsigned char> bytes = read_stream_bytes(image);
            std::size_t expected_size =
                static_cast<std::size_t>(width) * static_cast<std::size_t>(height) * 4U;
            if (bytes.size() != expected_size) {
                continue;
            }

            bool image_changed = false;
            for (std::size_t offset = 0; offset < bytes.size(); offset += 4U) {
                unsigned char& c = bytes[offset + 0];
                unsigned char& m = bytes[offset + 1];
                unsigned char& y = bytes[offset + 2];
                unsigned char& k = bytes[offset + 3];

                max_tac_before = std::max(max_tac_before, pixel_tac_percent(c, m, y, k));

                double cu = byte_to_unit(c);
                double mu = byte_to_unit(m);
                double yu = byte_to_unit(y);
                double ku = byte_to_unit(k);
                double total = cu + mu + yu + ku;

                if ((total * 100.0) <= max_tac + 0.01) {
                    max_tac_after = std::max(max_tac_after, total * 100.0);
                    continue;
                }

                if (ku >= max_tac_unit) {
                    cu = 0.0;
                    mu = 0.0;
                    yu = 0.0;
                    ku = max_tac_unit;
                } else {
                    double cmy_sum = cu + mu + yu;
                    if (cmy_sum > 0.0) {
                        double ratio = std::clamp((max_tac_unit - ku) / cmy_sum, 0.0, 1.0);
                        cu *= ratio;
                        mu *= ratio;
                        yu *= ratio;
                    }
                }

                c = unit_to_byte(cu);
                m = unit_to_byte(mu);
                y = unit_to_byte(yu);
                k = unit_to_byte(ku);
                max_tac_after = std::max(max_tac_after, pixel_tac_percent(c, m, y, k));
                ++pixels_modified;
                image_changed = true;
                page_changed = true;
            }

            if (image_changed) {
                image.replaceStreamData(
                    to_binary_string(bytes),
                    QPDFObjectHandle::newNull(),
                    QPDFObjectHandle::newNull());
                dict.removeKey("/Decode");
                dict.removeKey("/DecodeParms");
            }
        }

        if (page_changed) {
            pages_affected.insert(static_cast<int>(page_index + 1));
        }
    }

    record.success = pixels_modified > 0;
    if (record.success) {
        record.message = "Cobertura de tinta reduzida de " +
            std::to_string(static_cast<int>(std::lround(max_tac_before))) + "% para " +
            std::to_string(static_cast<int>(std::lround(max_tac_after))) +
            "% nas areas que excediam o limite.";
    } else {
        record.message = "Nao havia pixels CMYK acima do limite de TAC configurado.";
    }
    record.details["pixels_modified"] = std::to_string(pixels_modified);
    record.details["max_tac_before"] = std::to_string(max_tac_before);
    record.details["max_tac_after"] = std::to_string(max_tac_after);
    record.details["pages_affected"] = std::to_string(pages_affected.size());

    return record;
}

} // namespace printguard::fix

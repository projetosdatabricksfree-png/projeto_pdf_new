#include "printguard/fix/fixes/image_color_convert_fix.hpp"

#include "../color_transform_lcms.hpp"
#include "../pdf_color_utils.hpp"

#include <qpdf/QPDFObjectHandle.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <set>

namespace printguard::fix {

std::string ImageColorConvertFix::id() const {
    return "ImageColorConvertFix";
}

std::string ImageColorConvertFix::targets_finding_code() const {
    return "PG_ERR_RGB_COLORSPACE";
}

domain::FixRecord ImageColorConvertFix::apply(FixContext& ctx) const {
    domain::FixRecord record;
    record.fix_id = id();
    record.finding_code = targets_finding_code();
    record.attempted = true;
    record.status = "applied";

    RgbToCmykTransform transform(ctx.preset);
    int converted_images = 0;
    std::set<int> pages_affected;

    QPDFPageDocumentHelper doc_helper(ctx.pdf);
    auto pages = doc_helper.getAllPages();
    for (std::size_t page_index = 0; page_index < pages.size(); ++page_index) {
        auto& page = pages.at(page_index);
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

            std::string resolved_name;
            QPDFObjectHandle resolved_color_space =
                resolve_image_colorspace(page, dict, &resolved_name);
            if (!is_rgb_image_colorspace(resolved_color_space)) {
                continue;
            }

            int width = get_integer(dict, "/Width");
            int height = get_integer(dict, "/Height");
            int bits_per_component = get_integer(dict, "/BitsPerComponent");
            if (width <= 0 || height <= 0 || bits_per_component != 8) {
                continue;
            }

            std::vector<unsigned char> rgb_bytes = read_stream_bytes(image);
            std::size_t expected_size =
                static_cast<std::size_t>(width) * static_cast<std::size_t>(height) * 3U;
            if (rgb_bytes.size() != expected_size) {
                continue;
            }

            std::vector<unsigned char> cmyk_bytes = transform.convert_image(rgb_bytes);
            image.replaceStreamData(
                to_binary_string(cmyk_bytes),
                QPDFObjectHandle::newNull(),
                QPDFObjectHandle::newNull());

            dict.replaceKey("/ColorSpace", QPDFObjectHandle::newName("/DeviceCMYK"));
            dict.replaceKey("/BitsPerComponent", QPDFObjectHandle::newInteger(8));
            dict.removeKey("/Decode");
            dict.removeKey("/DecodeParms");

            ++converted_images;
            pages_affected.insert(static_cast<int>(page_index + 1));
        }
    }

    record.success = converted_images > 0;
    record.message = record.success ? "Imagens RGB foram convertidas para CMYK."
                                    : "Nao havia imagens RGB conversiveis no arquivo.";
    record.details["images_converted"] = std::to_string(converted_images);
    record.details["pages_affected"] = std::to_string(pages_affected.size());
    record.details["target_profile"] = transform.profile_name();

    return record;
}

} // namespace printguard::fix

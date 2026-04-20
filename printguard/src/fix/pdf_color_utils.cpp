#include "pdf_color_utils.hpp"

#include <fstream>
#include <iterator>
#include <stdexcept>

namespace printguard::fix {

namespace {

constexpr char kDefaultProfileName[] = "GRACoL2013.icc";

std::filesystem::path config_icc_directory() {
    return std::filesystem::path(PRINTGUARD_PROJECT_SOURCE_DIR) / "config" / "icc";
}

} // namespace

std::filesystem::path resolve_output_icc_profile_path(const domain::ProductPreset& preset) {
    std::string profile_name = resolve_output_icc_profile_name(preset);
    std::filesystem::path requested(profile_name);
    if (requested.is_absolute() && std::filesystem::exists(requested)) {
        return requested;
    }

    std::filesystem::path config_path = config_icc_directory() / profile_name;
    if (std::filesystem::exists(config_path)) {
        return config_path;
    }

    if (profile_name != kDefaultProfileName) {
        std::filesystem::path fallback = config_icc_directory() / kDefaultProfileName;
        if (std::filesystem::exists(fallback)) {
            return fallback;
        }
    }

    throw std::runtime_error("ICC profile not found: " + profile_name);
}

std::string resolve_output_icc_profile_name(const domain::ProductPreset& preset) {
    if (!preset.color_policy.output_intent_profile.empty()) {
        return preset.color_policy.output_intent_profile;
    }
    return kDefaultProfileName;
}

std::vector<unsigned char> load_output_icc_profile_bytes(const domain::ProductPreset& preset) {
    std::ifstream input(resolve_output_icc_profile_path(preset), std::ios::binary);
    if (!input) {
        throw std::runtime_error("Failed to open ICC profile from disk.");
    }

    return std::vector<unsigned char>(
        std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
}

int get_integer(QPDFObjectHandle dict, const std::string& key, int fallback) {
    QPDFObjectHandle value = dict.getKey(key);
    if (!value.isInteger()) {
        return fallback;
    }
    return value.getIntValueAsInt();
}

QPDFObjectHandle resolve_image_colorspace(
    QPDFPageObjectHelper& page,
    QPDFObjectHandle image_dict,
    std::string* resolved_name) {
    QPDFObjectHandle color_space = image_dict.getKey("/ColorSpace");
    if (!color_space.isName()) {
        return color_space;
    }

    if (resolved_name != nullptr) {
        *resolved_name = color_space.getName();
    }

    if (color_space.getName() == "/DeviceRGB" || color_space.getName() == "/DeviceGray" ||
        color_space.getName() == "/DeviceCMYK") {
        return color_space;
    }

    QPDFObjectHandle resources = page.getAttribute("/Resources", false);
    QPDFObjectHandle page_color_spaces = resources.getKey("/ColorSpace");
    if (page_color_spaces.isDictionary() && page_color_spaces.hasKey(color_space.getName())) {
        return page_color_spaces.getKey(color_space.getName());
    }

    return color_space;
}

bool is_rgb_image_colorspace(QPDFObjectHandle color_space) {
    if (color_space.isName()) {
        return color_space.getName() == "/DeviceRGB";
    }

    if (!color_space.isArray() || color_space.getArrayNItems() < 2) {
        return false;
    }

    QPDFObjectHandle kind = color_space.getArrayItem(0);
    if (!kind.isName() || kind.getName() != "/ICCBased") {
        return false;
    }

    QPDFObjectHandle profile = color_space.getArrayItem(1);
    if (!profile.isStream()) {
        return false;
    }

    return get_integer(profile.getDict(), "/N", 0) == 3;
}

bool is_device_cmyk_colorspace(QPDFObjectHandle color_space) {
    if (color_space.isName()) {
        return color_space.getName() == "/DeviceCMYK";
    }

    if (!color_space.isArray() || color_space.getArrayNItems() < 2) {
        return false;
    }

    QPDFObjectHandle kind = color_space.getArrayItem(0);
    if (!kind.isName() || kind.getName() != "/ICCBased") {
        return false;
    }

    QPDFObjectHandle profile = color_space.getArrayItem(1);
    if (!profile.isStream()) {
        return false;
    }

    return get_integer(profile.getDict(), "/N", 0) == 4;
}

std::vector<unsigned char> read_stream_bytes(QPDFObjectHandle stream) {
    auto data = stream.getStreamData(qpdf_dl_generalized);
    auto const* begin = reinterpret_cast<const unsigned char*>(data->getBuffer());
    return std::vector<unsigned char>(begin, begin + data->getSize());
}

std::string to_binary_string(const std::vector<unsigned char>& bytes) {
    return {reinterpret_cast<const char*>(bytes.data()), bytes.size()};
}

} // namespace printguard::fix

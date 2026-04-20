#include "color_transform_lcms.hpp"
#include "pdf_color_utils.hpp"

#include <algorithm>
#include <cmath>
#include <lcms2.h>
#include <stdexcept>

namespace printguard::fix {

namespace {

unsigned char to_byte(double value) {
    double clamped = std::clamp(value, 0.0, 1.0);
    return static_cast<unsigned char>(std::lround(clamped * 255.0));
}

double to_unit(unsigned char value) {
    return static_cast<double>(value) / 255.0;
}

} // namespace

struct RgbToCmykTransform::Impl {
    explicit Impl(const domain::ProductPreset& preset) :
        profile_name(resolve_output_icc_profile_name(preset)),
        profile_path(resolve_output_icc_profile_path(preset)),
        source_profile(cmsCreate_sRGBProfile()),
        target_profile(cmsOpenProfileFromFile(profile_path.string().c_str(), "r")),
        transform(nullptr) {
        if (source_profile == nullptr) {
            throw std::runtime_error("Failed to create sRGB profile.");
        }
        if (target_profile == nullptr) {
            cmsCloseProfile(source_profile);
            throw std::runtime_error("Failed to open CMYK ICC profile: " + profile_path.string());
        }

        transform = cmsCreateTransform(
            source_profile,
            TYPE_RGB_8,
            target_profile,
            TYPE_CMYK_8,
            INTENT_PERCEPTUAL,
            0);
        if (transform == nullptr) {
            cmsCloseProfile(target_profile);
            cmsCloseProfile(source_profile);
            throw std::runtime_error("Failed to create RGB to CMYK transform.");
        }
    }

    ~Impl() {
        if (transform != nullptr) {
            cmsDeleteTransform(transform);
        }
        if (target_profile != nullptr) {
            cmsCloseProfile(target_profile);
        }
        if (source_profile != nullptr) {
            cmsCloseProfile(source_profile);
        }
    }

    std::string profile_name;
    std::filesystem::path profile_path;
    cmsHPROFILE source_profile;
    cmsHPROFILE target_profile;
    cmsHTRANSFORM transform;
};

RgbToCmykTransform::RgbToCmykTransform(const domain::ProductPreset& preset) :
    impl_(std::make_unique<Impl>(preset)) {}

RgbToCmykTransform::~RgbToCmykTransform() = default;

std::array<unsigned char, 4> RgbToCmykTransform::convert_pixel(
    std::array<unsigned char, 3> const& rgb) const {
    std::array<unsigned char, 4> cmyk{};
    cmsDoTransform(impl_->transform, rgb.data(), cmyk.data(), 1);
    return cmyk;
}

CmykColor RgbToCmykTransform::convert_operator_color(double r, double g, double b) const {
    auto cmyk = convert_pixel({to_byte(r), to_byte(g), to_byte(b)});
    return {to_unit(cmyk[0]), to_unit(cmyk[1]), to_unit(cmyk[2]), to_unit(cmyk[3])};
}

std::vector<unsigned char> RgbToCmykTransform::convert_image(
    std::vector<unsigned char> const& rgb_bytes) const {
    if ((rgb_bytes.size() % 3U) != 0U) {
        throw std::runtime_error("RGB image data size is not divisible by 3.");
    }

    std::vector<unsigned char> cmyk_bytes((rgb_bytes.size() / 3U) * 4U);
    cmsDoTransform(
        impl_->transform,
        rgb_bytes.data(),
        cmyk_bytes.data(),
        static_cast<unsigned int>(rgb_bytes.size() / 3U));
    return cmyk_bytes;
}

std::string const& RgbToCmykTransform::profile_name() const {
    return impl_->profile_name;
}

} // namespace printguard::fix

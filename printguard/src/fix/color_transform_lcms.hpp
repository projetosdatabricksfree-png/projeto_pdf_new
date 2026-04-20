#pragma once

#include "printguard/domain/preset.hpp"

#include <array>
#include <memory>
#include <string>
#include <vector>

namespace printguard::fix {

struct CmykColor {
    double c = 0.0;
    double m = 0.0;
    double y = 0.0;
    double k = 0.0;
};

class RgbToCmykTransform {
public:
    explicit RgbToCmykTransform(const domain::ProductPreset& preset);
    ~RgbToCmykTransform();

    RgbToCmykTransform(RgbToCmykTransform const&) = delete;
    RgbToCmykTransform& operator=(RgbToCmykTransform const&) = delete;

    [[nodiscard]] std::array<unsigned char, 4> convert_pixel(
        std::array<unsigned char, 3> const& rgb) const;
    [[nodiscard]] CmykColor convert_operator_color(double r, double g, double b) const;
    [[nodiscard]] std::vector<unsigned char> convert_image(
        std::vector<unsigned char> const& rgb_bytes) const;
    [[nodiscard]] std::string const& profile_name() const;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace printguard::fix

#pragma once

#include <string>

namespace printguard::render {

struct PreviewResult {
    bool generated = false;
    std::string output_path;
    std::string warning;
    long long duration_ms = 0;
};

class PreviewRenderer {
public:
    PreviewResult render_first_page(
        const std::string& input_pdf,
        const std::string& output_png,
        int width_pixels = 1200,
        int timeout_seconds = 30) const;
};

} // namespace printguard::render

#include "printguard/render/preview_renderer.hpp"

#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <sstream>

namespace printguard::render {

namespace {

std::string shell_escape(std::string const& input) {
    std::string escaped = "'";
    for (char ch : input) {
        if (ch == '\'') {
            escaped += "'\\''";
        } else {
            escaped += ch;
        }
    }
    escaped += "'";
    return escaped;
}

} // namespace

PreviewResult PreviewRenderer::render_first_page(
    const std::string& input_pdf,
    const std::string& output_png,
    int width_pixels,
    int timeout_seconds) const {
    PreviewResult result;
    auto started_at = std::chrono::steady_clock::now();

    std::filesystem::create_directories(std::filesystem::path(output_png).parent_path());

    std::ostringstream command;
    command << "timeout " << timeout_seconds << "s mutool draw -q -w " << width_pixels
            << " -o " << shell_escape(output_png) << ' ' << shell_escape(input_pdf) << " 1 >/dev/null 2>&1";

    int rc = std::system(command.str().c_str());
    result.duration_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                             std::chrono::steady_clock::now() - started_at)
                             .count();

    if (rc == 0 && std::filesystem::exists(output_png)) {
        result.generated = true;
        result.output_path = output_png;
        return result;
    }

    result.warning = "Preview nao gerado pelo mutool.";
    return result;
}

} // namespace printguard::render

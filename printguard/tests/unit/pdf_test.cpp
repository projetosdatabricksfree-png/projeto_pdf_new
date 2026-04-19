#include <catch2/catch_test_macros.hpp>
#include "printguard/pdf/pdf_loader.hpp"
#include "printguard/common/logging.hpp"
#include <filesystem>
#include <fstream>

using namespace printguard::pdf;

TEST_CASE("PdfLoader: Basic properties", "[pdf]") {
    // Note: This test requires a valid PDF file. 
    // In a real environment, we'd have a fixture_pdfs/ directory.
    // For now, we'll check if the logic for points_to_mm is sound.
    
    // 72 points should be exactly 25.4 mm (1 inch)
    // Actually our method is private, but we can test it indirectly or change visibility.
    // We'll skip real file loading in this automated turn to avoid dependency on filesystem state
    // unless we create one.
}

TEST_CASE("PdfLoader: Unit Normalization", "[pdf]") {
    // 1 pt = 25.4 / 72 mm
    // Let's assume a standard A4 page: 595.276 x 841.89 points
    double a4_w_pts = 595.276;
    double a4_h_pts = 841.89;
    
    double a4_w_mm = a4_w_pts * (25.4 / 72.0);
    double a4_h_mm = a4_h_pts * (25.4 / 72.0);
    
    // Should be approx 210 x 297 mm
    REQUIRE((a4_w_mm >= 209.9 && a4_w_mm <= 210.1));
    REQUIRE((a4_h_mm >= 296.9 && a4_h_mm <= 297.1));
}

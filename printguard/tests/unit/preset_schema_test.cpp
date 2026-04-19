#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "printguard/domain/config_loader.hpp"
#include "printguard/domain/preset.hpp"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <string>

#include <unistd.h>

namespace {

namespace fs = std::filesystem;

struct TempDir {
    fs::path path;
    ~TempDir() {
        if (!path.empty()) {
            std::error_code ec;
            fs::remove_all(path, ec);
        }
    }
};

TempDir make_temp_dir() {
    auto suffix = std::to_string(getpid()) + "_" +
                  std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
    fs::path path = fs::temp_directory_path() / ("printguard_preset_schema_" + suffix);
    fs::create_directories(path);
    return TempDir{path};
}

void write_file(fs::path const& path, std::string const& content) {
    std::ofstream out(path, std::ios::binary);
    out << content;
}

} // namespace

TEST_CASE("ConfigLoader: legacy preset loads with defaults", "[domain][preset]") {
    auto tmp = make_temp_dir();

    write_file(tmp.path / "legacy.json", R"json(
{
  "id": "legacy",
  "name": "Legacy Preset",
  "width_mm": 100.0,
  "height_mm": 200.0,
  "bleed_mm": 2.0,
  "min_dpi": 240,
  "allowed_color_spaces": ["CMYK"]
}
)json");

    auto presets = printguard::domain::ConfigLoader::load_presets(tmp.path.string());
    REQUIRE(presets.contains("legacy"));

    auto const& preset = presets.at("legacy");
    REQUIRE(preset.id == "legacy");
    REQUIRE(preset.name == "Legacy Preset");
    REQUIRE(preset.final_width_mm == Catch::Approx(100.0));
    REQUIRE(preset.final_height_mm == Catch::Approx(200.0));
    REQUIRE(preset.bleed_mm == Catch::Approx(2.0));
    REQUIRE(preset.min_effective_dpi == 240);
    REQUIRE(preset.family == printguard::domain::ProductFamily::quick_print);

    REQUIRE(preset.color_policy.target_output == "CMYK");
    REQUIRE(preset.color_policy.allow_rgb_images == false);
    REQUIRE(preset.color_policy.require_output_intent == true);
    REQUIRE(preset.color_policy.output_intent_profile == "GRACoL2013.icc");

    REQUIRE(preset.geometry_policy.require_trimbox == true);
    REQUIRE(preset.geometry_policy.auto_normalize_boxes == true);
}

TEST_CASE("ConfigLoader: expanded preset loads nested policies", "[domain][preset]") {
    auto tmp = make_temp_dir();

    write_file(tmp.path / "expanded.json", R"json(
{
  "id": "expanded",
  "name": "Expanded Preset",
  "family": "labels_and_stickers",
  "description": "preset completo",
  "orientation": "portrait",
  "final_width_mm": 55.0,
  "final_height_mm": 85.0,
  "bleed_mm": 3.0,
  "safe_margin_mm": 4.0,
  "expected_pages_min": 1,
  "expected_pages_max": 10,
  "duplex_allowed": true,
  "imposition_style": "none",
  "min_effective_dpi": 300,
  "warning_effective_dpi": 450,
  "max_total_ink_percent": 280,
  "notes": "ok",
  "color_policy": {
    "allow_rgb_images": true,
    "allow_rgb_vectors": true,
    "allow_spot_colors": true,
    "require_output_intent": false
  },
  "geometry_policy": {
    "require_trimbox": true,
    "require_bleedbox": false,
    "auto_create_bleedbox_if_safe": false,
    "auto_normalize_boxes": false,
    "allow_missing_bleed_for_document_products": true
  },
  "transparency_policy": {
    "allow_transparency": true,
    "flatten_automatically": false,
    "manual_review_if_complex": true
  },
  "text_policy": {
    "min_black_text_overprint_pt": 9.0,
    "min_multicolor_text_size_pt": 6.0,
    "normalize_rich_black_small_text": false,
    "forbid_white_overprint": false
  },
  "fix_policy": {
    "auto_fix_rgb_to_cmyk": false,
    "auto_normalize_boxes": false,
    "auto_remove_annotations": false
  },
  "manual_review_policy": {
    "manual_review_on_low_resolution_below_error": false
  }
}
)json");

    auto presets = printguard::domain::ConfigLoader::load_presets(tmp.path.string());
    REQUIRE(presets.contains("expanded"));

    auto const& preset = presets.at("expanded");
    REQUIRE(preset.family == printguard::domain::ProductFamily::labels_and_stickers);
    REQUIRE(preset.description == "preset completo");
    REQUIRE(preset.orientation == "portrait");
    REQUIRE(preset.safe_margin_mm == Catch::Approx(4.0));
    REQUIRE(preset.expected_pages_max == 10);
    REQUIRE(preset.duplex_allowed == true);
    REQUIRE(preset.max_total_ink_percent == 280);

    REQUIRE(preset.color_policy.allow_rgb_images == true);
    REQUIRE(preset.color_policy.allow_spot_colors == true);
    REQUIRE(preset.color_policy.require_output_intent == false);

    REQUIRE(preset.geometry_policy.require_bleedbox == false);
    REQUIRE(preset.geometry_policy.auto_normalize_boxes == false);
    REQUIRE(preset.geometry_policy.allow_missing_bleed_for_document_products == true);

    REQUIRE(preset.text_policy.min_black_text_overprint_pt == Catch::Approx(9.0));
    REQUIRE(preset.text_policy.normalize_rich_black_small_text == false);

    REQUIRE(preset.fix_policy.auto_fix_rgb_to_cmyk == false);
    REQUIRE(preset.fix_policy.auto_remove_annotations == false);

    REQUIRE(preset.manual_review_policy.manual_review_on_low_resolution_below_error == false);
}

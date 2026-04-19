#pragma once

#include <string>
#include <vector>

namespace printguard::domain {

enum class ProductFamily {
    quick_print,
    documents_and_books,
    signage_and_large_format,
    labels_and_stickers,
};

inline ProductFamily product_family_from_string(std::string const& value) {
    if (value == "documents_and_books") {
        return ProductFamily::documents_and_books;
    }
    if (value == "signage_and_large_format") {
        return ProductFamily::signage_and_large_format;
    }
    if (value == "labels_and_stickers") {
        return ProductFamily::labels_and_stickers;
    }
    return ProductFamily::quick_print;
}

inline std::string product_family_to_string(ProductFamily value) {
    switch (value) {
        case ProductFamily::quick_print:
            return "quick_print";
        case ProductFamily::documents_and_books:
            return "documents_and_books";
        case ProductFamily::signage_and_large_format:
            return "signage_and_large_format";
        case ProductFamily::labels_and_stickers:
            return "labels_and_stickers";
    }
    return "quick_print";
}

struct ColorPolicy {
    std::string target_output = "CMYK";
    bool allow_rgb_images = false;
    bool allow_rgb_vectors = false;
    bool allow_spot_colors = false;
    bool allow_device_gray = true;
    bool require_output_intent = true;
    std::string output_intent_profile = "GRACoL2013.icc";
};

struct GeometryPolicy {
    bool require_trimbox = true;
    bool require_bleedbox = true;
    bool auto_create_bleedbox_if_safe = true;
    bool auto_normalize_boxes = true;
    bool allow_missing_bleed_for_document_products = false;
};

struct TransparencyPolicy {
    bool allow_transparency = true;
    bool flatten_automatically = false;
    bool manual_review_if_complex = true;
};

struct TextPolicy {
    double min_black_text_overprint_pt = 12.0;
    double min_multicolor_text_size_pt = 5.0;
    bool normalize_rich_black_small_text = true;
    bool forbid_white_overprint = true;
};

struct FixPolicy {
    bool auto_fix_rgb_to_cmyk = true;
    bool auto_fix_spot_to_cmyk = true;
    bool auto_attach_output_intent = true;
    bool auto_normalize_boxes = true;
    bool auto_rotate_pages = true;
    bool auto_remove_white_overprint = true;
    bool auto_remove_annotations = true;
    bool auto_remove_layers_when_safe = true;
    bool auto_reduce_tac = true;
    bool auto_normalize_black = true;
};

struct ManualReviewPolicy {
    bool manual_review_on_safety_margin_violation = true;
    bool manual_review_on_visual_bleed_missing = true;
    bool manual_review_on_complex_transparency = true;
    bool manual_review_on_font_embedding_issue = true;
    bool manual_review_on_low_resolution_below_error = true;
};

struct ProductPreset {
    std::string id;
    std::string name;
    ProductFamily family = ProductFamily::quick_print;
    std::string description;
    std::string orientation = "auto";
    double final_width_mm = 0.0;
    double final_height_mm = 0.0;
    double bleed_mm = 3.0;
    double safe_margin_mm = 0.0;
    int expected_pages_min = 1;
    int expected_pages_max = 1;
    bool duplex_allowed = false;
    std::string imposition_style = "none";
    int min_effective_dpi = 300;
    int warning_effective_dpi = 450;
    int max_total_ink_percent = 320;
    std::string notes;

    ColorPolicy color_policy{};
    GeometryPolicy geometry_policy{};
    TransparencyPolicy transparency_policy{};
    TextPolicy text_policy{};
    FixPolicy fix_policy{};
    ManualReviewPolicy manual_review_policy{};

    std::vector<std::string> allowed_color_spaces = {"CMYK", "Gray"};
};

} // namespace printguard::domain

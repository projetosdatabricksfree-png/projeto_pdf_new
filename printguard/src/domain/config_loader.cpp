#include "printguard/domain/config_loader.hpp"
#include "printguard/common/logging.hpp"
#include <nlohmann/json.hpp>
#include <fstream>
#include <filesystem>

using json = nlohmann::json;

namespace printguard::domain {

std::map<std::string, ProductPreset> ConfigLoader::load_presets(const std::string& path) {
    std::map<std::string, ProductPreset> presets;

    for (const auto& entry : std::filesystem::recursive_directory_iterator(path)) {
        if (entry.path().extension() == ".json") {
            std::ifstream f(entry.path());
            try {
                json data = json::parse(f);
                ProductPreset p;

                p.id = data.value("id", std::string{});
                p.name = data.value("name", std::string{});
                if (p.id.empty() || p.name.empty()) {
                    throw std::runtime_error("Preset sem id/nome obrigatorios.");
                }

                p.final_width_mm = data.value("final_width_mm", data.value("width_mm", p.final_width_mm));
                p.final_height_mm =
                    data.value("final_height_mm", data.value("height_mm", p.final_height_mm));

                p.bleed_mm = data.value("bleed_mm", p.bleed_mm);
                p.min_effective_dpi =
                    data.value("min_effective_dpi", data.value("min_dpi", p.min_effective_dpi));

                p.allowed_color_spaces = data.value("allowed_color_spaces", p.allowed_color_spaces);

                p.description = data.value("description", p.description);
                p.orientation = data.value("orientation", p.orientation);
                p.safe_margin_mm = data.value("safe_margin_mm", p.safe_margin_mm);
                p.expected_pages_min = data.value("expected_pages_min", p.expected_pages_min);
                p.expected_pages_max = data.value("expected_pages_max", p.expected_pages_max);
                p.duplex_allowed = data.value("duplex_allowed", p.duplex_allowed);
                p.imposition_style = data.value("imposition_style", p.imposition_style);
                p.warning_effective_dpi = data.value("warning_effective_dpi", p.warning_effective_dpi);
                p.max_total_ink_percent = data.value("max_total_ink_percent", p.max_total_ink_percent);
                p.notes = data.value("notes", p.notes);

                p.family = product_family_from_string(
                    data.value("family", product_family_to_string(p.family)));

                if (auto it = data.find("color_policy"); it != data.end() && it->is_object()) {
                    auto const& policy = *it;
                    p.color_policy.target_output =
                        policy.value("target_output", p.color_policy.target_output);
                    p.color_policy.allow_rgb_images =
                        policy.value("allow_rgb_images", p.color_policy.allow_rgb_images);
                    p.color_policy.allow_rgb_vectors =
                        policy.value("allow_rgb_vectors", p.color_policy.allow_rgb_vectors);
                    p.color_policy.allow_spot_colors =
                        policy.value("allow_spot_colors", p.color_policy.allow_spot_colors);
                    p.color_policy.allow_device_gray =
                        policy.value("allow_device_gray", p.color_policy.allow_device_gray);
                    p.color_policy.require_output_intent =
                        policy.value("require_output_intent", p.color_policy.require_output_intent);
                    p.color_policy.output_intent_profile =
                        policy.value("output_intent_profile", p.color_policy.output_intent_profile);
                }

                if (auto it = data.find("geometry_policy"); it != data.end() && it->is_object()) {
                    auto const& policy = *it;
                    p.geometry_policy.require_trimbox =
                        policy.value("require_trimbox", p.geometry_policy.require_trimbox);
                    p.geometry_policy.require_bleedbox =
                        policy.value("require_bleedbox", p.geometry_policy.require_bleedbox);
                    p.geometry_policy.auto_create_bleedbox_if_safe = policy.value(
                        "auto_create_bleedbox_if_safe",
                        p.geometry_policy.auto_create_bleedbox_if_safe);
                    p.geometry_policy.auto_normalize_boxes =
                        policy.value("auto_normalize_boxes", p.geometry_policy.auto_normalize_boxes);
                    p.geometry_policy.allow_missing_bleed_for_document_products = policy.value(
                        "allow_missing_bleed_for_document_products",
                        p.geometry_policy.allow_missing_bleed_for_document_products);
                }

                if (auto it = data.find("transparency_policy"); it != data.end() && it->is_object()) {
                    auto const& policy = *it;
                    p.transparency_policy.allow_transparency =
                        policy.value("allow_transparency", p.transparency_policy.allow_transparency);
                    p.transparency_policy.flatten_automatically = policy.value(
                        "flatten_automatically", p.transparency_policy.flatten_automatically);
                    p.transparency_policy.manual_review_if_complex = policy.value(
                        "manual_review_if_complex", p.transparency_policy.manual_review_if_complex);
                }

                if (auto it = data.find("text_policy"); it != data.end() && it->is_object()) {
                    auto const& policy = *it;
                    p.text_policy.min_black_text_overprint_pt = policy.value(
                        "min_black_text_overprint_pt",
                        p.text_policy.min_black_text_overprint_pt);
                    p.text_policy.min_multicolor_text_size_pt = policy.value(
                        "min_multicolor_text_size_pt", p.text_policy.min_multicolor_text_size_pt);
                    p.text_policy.normalize_rich_black_small_text = policy.value(
                        "normalize_rich_black_small_text",
                        p.text_policy.normalize_rich_black_small_text);
                    p.text_policy.forbid_white_overprint =
                        policy.value("forbid_white_overprint", p.text_policy.forbid_white_overprint);
                }

                if (auto it = data.find("fix_policy"); it != data.end() && it->is_object()) {
                    auto const& policy = *it;
                    p.fix_policy.auto_fix_rgb_to_cmyk =
                        policy.value("auto_fix_rgb_to_cmyk", p.fix_policy.auto_fix_rgb_to_cmyk);
                    p.fix_policy.auto_fix_spot_to_cmyk =
                        policy.value("auto_fix_spot_to_cmyk", p.fix_policy.auto_fix_spot_to_cmyk);
                    p.fix_policy.auto_attach_output_intent = policy.value(
                        "auto_attach_output_intent", p.fix_policy.auto_attach_output_intent);
                    p.fix_policy.auto_normalize_boxes =
                        policy.value("auto_normalize_boxes", p.fix_policy.auto_normalize_boxes);
                    p.fix_policy.auto_rotate_pages =
                        policy.value("auto_rotate_pages", p.fix_policy.auto_rotate_pages);
                    p.fix_policy.auto_remove_white_overprint = policy.value(
                        "auto_remove_white_overprint", p.fix_policy.auto_remove_white_overprint);
                    p.fix_policy.auto_remove_annotations =
                        policy.value("auto_remove_annotations", p.fix_policy.auto_remove_annotations);
                    p.fix_policy.auto_remove_layers_when_safe = policy.value(
                        "auto_remove_layers_when_safe", p.fix_policy.auto_remove_layers_when_safe);
                    p.fix_policy.auto_reduce_tac =
                        policy.value("auto_reduce_tac", p.fix_policy.auto_reduce_tac);
                    p.fix_policy.auto_normalize_black =
                        policy.value("auto_normalize_black", p.fix_policy.auto_normalize_black);
                }

                if (auto it = data.find("manual_review_policy"); it != data.end() && it->is_object()) {
                    auto const& policy = *it;
                    p.manual_review_policy.manual_review_on_safety_margin_violation = policy.value(
                        "manual_review_on_safety_margin_violation",
                        p.manual_review_policy.manual_review_on_safety_margin_violation);
                    p.manual_review_policy.manual_review_on_visual_bleed_missing = policy.value(
                        "manual_review_on_visual_bleed_missing",
                        p.manual_review_policy.manual_review_on_visual_bleed_missing);
                    p.manual_review_policy.manual_review_on_complex_transparency = policy.value(
                        "manual_review_on_complex_transparency",
                        p.manual_review_policy.manual_review_on_complex_transparency);
                    p.manual_review_policy.manual_review_on_font_embedding_issue = policy.value(
                        "manual_review_on_font_embedding_issue",
                        p.manual_review_policy.manual_review_on_font_embedding_issue);
                    p.manual_review_policy.manual_review_on_low_resolution_below_error = policy.value(
                        "manual_review_on_low_resolution_below_error",
                        p.manual_review_policy.manual_review_on_low_resolution_below_error);
                }
                
                presets[p.id] = p;
                PG_LOG_INFO("Loaded preset: {}", p.id);
            } catch (const std::exception& e) {
                PG_LOG_ERROR("Failed to load preset {}: {}", entry.path().string(), e.what());
            }
        }
    }
    return presets;
}

std::map<std::string, ValidationProfile> ConfigLoader::load_profiles(const std::string& path) {
    std::map<std::string, ValidationProfile> profiles;

    for (const auto& entry : std::filesystem::directory_iterator(path)) {
        if (entry.path().extension() == ".json") {
            std::ifstream f(entry.path());
            try {
                json data = json::parse(f);
                ValidationProfile p;
                p.id = data["id"];
                p.name = data["name"];
                p.description = data.value("description", std::string{});

                for (auto& [rule_id, rule_data] : data["rules"].items()) {
                    RuleConfig rc;
                    rc.enabled = rule_data["enabled"];
                    rc.severity = severity_from_string(rule_data.value("severity", "WARNING"));
                    if (rule_data.contains("params")) {
                        rc.params = rule_data["params"].get<std::map<std::string, std::string>>();
                    }
                    p.rules[rule_id] = rc;
                }

                profiles[p.id] = p;
                PG_LOG_INFO("Loaded profile: {}", p.id);
            } catch (const std::exception& e) {
                PG_LOG_ERROR("Failed to load profile {}: {}", entry.path().string(), e.what());
            }
        }
    }
    return profiles;
}

RuleSeverity ConfigLoader::severity_from_string(const std::string& s) {
    if (s == "INFO") return RuleSeverity::INFO;
    if (s == "ERROR") return RuleSeverity::ERROR;
    return RuleSeverity::WARNING;
}

} // namespace printguard::domain

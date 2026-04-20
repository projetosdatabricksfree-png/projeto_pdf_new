#include "printguard/fix/fix_engine.hpp"

#include "printguard/common/logging.hpp"
#include "printguard/fix/fixes/attach_output_intent_fix.hpp"
#include "printguard/fix/fixes/black_normalization_fix.hpp"
#include "printguard/fix/fixes/convert_rgb_to_cmyk_fix.hpp"
#include "printguard/fix/fixes/flatten_layers_fix.hpp"
#include "printguard/fix/fixes/image_color_convert_fix.hpp"
#include "printguard/fix/fixes/normalize_boxes_fix.hpp"
#include "printguard/fix/fixes/remove_annotations_fix.hpp"
#include "printguard/fix/fixes/remove_white_overprint_fix.hpp"
#include "printguard/fix/fixes/rotation_fix.hpp"
#include "printguard/fix/fixes/spot_color_conversion_fix.hpp"
#include "printguard/fix/fixes/tac_reduction_fix.hpp"
#include <algorithm>
#include <functional>
#include <filesystem>
#include <map>
#include <set>
#include <qpdf/QPDF.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFWriter.hh>

namespace printguard::fix {

namespace {

void write_pdf(QPDF& pdf, const std::filesystem::path& output_path) {
    QPDFWriter writer(pdf, output_path.string().c_str());
    writer.setStaticID(true);
    writer.write();
}

void validate_output(const std::filesystem::path& path) {
    QPDF validation;
    validation.processFile(path.string().c_str());
}

using FixPolicyAccessor = bool (*)(const domain::FixPolicy&);
using ManualReviewAccessor = bool (*)(const domain::ManualReviewPolicy&);

struct ManualReviewDecision {
    bool recognized = false;
    bool enabled = false;
    std::string reason;
};

std::string summarize_finding(const domain::Finding& finding) {
    if (!finding.user_message.empty()) {
        return finding.user_message;
    }
    if (!finding.technical_message.empty()) {
        return finding.technical_message;
    }
    return finding.code;
}

FixPolicyAccessor fix_policy_accessor_for(std::string const& finding_code) {
    static const std::map<std::string, FixPolicyAccessor> kMapping = {
        {"PG_ERR_RGB_COLORSPACE",
         [](const domain::FixPolicy& policy) { return policy.auto_fix_rgb_to_cmyk; }},
        {"PG_ERR_MISSING_BLEED_BOX",
         [](const domain::FixPolicy& policy) { return policy.auto_normalize_boxes; }},
        {"PG_ERR_MISSING_OUTPUT_INTENT",
         [](const domain::FixPolicy& policy) { return policy.auto_attach_output_intent; }},
        {"PG_ERR_TAC_EXCEEDED",
         [](const domain::FixPolicy& policy) { return policy.auto_reduce_tac; }},
        {"PG_ERR_WHITE_OVERPRINT",
         [](const domain::FixPolicy& policy) { return policy.auto_remove_white_overprint; }},
        {"PG_WARN_RICH_BLACK_TEXT",
         [](const domain::FixPolicy& policy) { return policy.auto_normalize_black; }},
        {"PG_WARN_ANNOTATIONS",
         [](const domain::FixPolicy& policy) { return policy.auto_remove_annotations; }},
        {"PG_WARN_LAYERS_PRESENT",
         [](const domain::FixPolicy& policy) { return policy.auto_remove_layers_when_safe; }},
        {"PG_WARN_SPOT_COLORS",
         [](const domain::FixPolicy& policy) { return policy.auto_fix_spot_to_cmyk; }},
        {"PG_WARN_ROTATION_MISMATCH",
         [](const domain::FixPolicy& policy) { return policy.auto_rotate_pages; }},
    };

    auto it = kMapping.find(finding_code);
    return it == kMapping.end() ? nullptr : it->second;
}

ManualReviewDecision manual_review_decision_for(
    const domain::Finding& finding,
    const domain::ProductPreset& preset) {
    auto const& policy = preset.manual_review_policy;

    if (finding.code == "PG_ERR_SAFETY_MARGIN") {
        return {
            true,
            policy.manual_review_on_safety_margin_violation,
            "Violacao de safety margin requer revisao manual: " + summarize_finding(finding)};
    }

    if (finding.code == "PG_WARN_TRANSPARENCY") {
        return {
            true,
            policy.manual_review_on_complex_transparency,
            "Transparencia complexa requer revisao manual: " + summarize_finding(finding)};
    }

    if (finding.code == "PG_ERR_LOW_RES" && finding.severity == domain::FindingSeverity::ERROR) {
        return {
            true,
            policy.manual_review_on_low_resolution_below_error,
            "Resolucao abaixo do minimo requer revisao manual: " + summarize_finding(finding)};
    }

    if ((finding.code == "PG_ERR_MISSING_BLEED_BOX" || finding.code == "PG_ERR_BLEED_INSUFFICIENT") &&
        preset.bleed_mm > 0.0) {
        return {
            true,
            policy.manual_review_on_visual_bleed_missing,
            "Problema de bleed requer revisao manual: " + summarize_finding(finding)};
    }

    if ((finding.code == "PG_ERR_MISSING_BLEED_BOX" || finding.code == "PG_ERR_BLEED_INSUFFICIENT") &&
        preset.bleed_mm <= 0.0) {
        return {true, false, {}};
    }

    if (finding.code == "PG_ERR_FONT_NOT_EMBEDDED") {
        return {
            true,
            policy.manual_review_on_font_embedding_issue,
            "Fonte nao embutida requer revisao manual: " + summarize_finding(finding)};
    }

    return {};
}

void append_unique(std::vector<std::string>& items, std::set<std::string>& seen, std::string value) {
    if (seen.insert(value).second) {
        items.push_back(std::move(value));
    }
}

} // namespace

void FixEngine::register_fix(std::unique_ptr<IFix> fix) {
    m_fixes.push_back(std::move(fix));
}

FixPlan FixPlanner::build_plan(
    const std::vector<domain::Finding>& findings,
    const FixEngine& engine,
    const domain::ProductPreset& preset) const {
    FixPlan plan;
    std::set<std::string> action_dedupe;
    std::set<std::string> skipped_dedupe;
    std::set<std::string> unresolved_dedupe;
    std::set<std::string> manual_reason_dedupe;

    for (const auto& finding : findings) {
        std::vector<std::string> matching_fix_ids;
        for (const auto& fix : engine.m_fixes) {
            if (fix->targets_finding_code() == finding.code) {
                matching_fix_ids.push_back(fix->id());
            }
        }

        bool resolved_by_plan = false;
        bool has_fix_policy_mapping = false;
        if (finding.fixability == domain::Fixability::AUTOMATIC_SAFE) {
            if (auto accessor = fix_policy_accessor_for(finding.code)) {
                has_fix_policy_mapping = true;
                bool enabled = accessor(preset.fix_policy);
                if (!matching_fix_ids.empty() && enabled) {
                    for (auto const& fix_id : matching_fix_ids) {
                        append_unique(plan.actions, action_dedupe, fix_id);
                    }
                    resolved_by_plan = true;
                } else if (!matching_fix_ids.empty()) {
                    append_unique(
                        plan.skipped_fixes,
                        skipped_dedupe,
                        finding.code + ": fix automatica desabilitada pelo preset.");
                } else {
                    append_unique(
                        plan.skipped_fixes,
                        skipped_dedupe,
                        finding.code + ": nenhum fix registrado para este finding.");
                }
            }
        }

        if (!resolved_by_plan) {
            append_unique(plan.unresolved_finding_codes, unresolved_dedupe, finding.code);
            if (finding.is_blocking()) {
                plan.has_blocking_unresolved = true;
            }
        }

        auto review = manual_review_decision_for(finding, preset);
        if (review.enabled) {
            plan.needs_manual_review = true;
            append_unique(plan.manual_review_reasons, manual_reason_dedupe, review.reason);
        } else if (!resolved_by_plan && finding.is_blocking() &&
                   finding.fixability != domain::Fixability::AUTOMATIC_SAFE &&
                   !review.recognized) {
            plan.needs_manual_review = true;
            append_unique(
                plan.manual_review_reasons,
                manual_reason_dedupe,
                "Finding blocking sem correcao automatica segura: " + summarize_finding(finding));
        } else if (!resolved_by_plan && finding.is_blocking() &&
                   finding.fixability == domain::Fixability::AUTOMATIC_SAFE &&
                   !matching_fix_ids.empty() &&
                   !has_fix_policy_mapping &&
                   !review.recognized) {
            plan.needs_manual_review = true;
            append_unique(
                plan.manual_review_reasons,
                manual_reason_dedupe,
                "Fix automatico desabilitado pelo preset para finding blocking: " +
                    summarize_finding(finding));
        } else if (!resolved_by_plan && finding.is_blocking() && matching_fix_ids.empty() &&
                   !has_fix_policy_mapping &&
                   !review.recognized) {
            plan.needs_manual_review = true;
            append_unique(
                plan.manual_review_reasons,
                manual_reason_dedupe,
                "Finding blocking sem fix disponivel: " + summarize_finding(finding));
        }
    }

    plan.status = plan.needs_manual_review ? "manual_review_required" : "completed";

    return plan;
}

FixExecutionResult FixEngine::execute(
    const std::string& input_pdf,
    const std::string& output_pdf,
    const FixPlan& plan,
    const std::vector<domain::Finding>& findings,
    const domain::ProductPreset& preset) const {
    FixExecutionResult result;
    result.output_path = output_pdf;

    std::filesystem::create_directories(std::filesystem::path(output_pdf).parent_path());

    if (plan.actions.empty()) {
        std::filesystem::copy_file(
            input_pdf, output_pdf, std::filesystem::copy_options::overwrite_existing);
        result.output_generated = true;
        return result;
    }

    QPDF pdf;
    pdf.processFile(input_pdf.c_str());
    bool changed = false;

    FixContext context{pdf, preset, findings};

    // Apply registered fixes that are in the plan
    for (const auto& fix : m_fixes) {
        auto fix_id = fix->id();
        auto it = std::find(plan.actions.begin(), plan.actions.end(), fix_id);
        if (it != plan.actions.end()) {
            auto record = fix->apply(context);
            result.records.push_back(record);
            changed = changed || record.success;
        }
    }

    if (!changed) {
        std::filesystem::copy_file(
            input_pdf, output_pdf, std::filesystem::copy_options::overwrite_existing);
        result.output_generated = true;
        return result;
    }

    std::filesystem::path output_path(output_pdf);
    std::filesystem::path temp_path = output_path;
    temp_path += ".tmp";

    write_pdf(pdf, temp_path);
    validate_output(temp_path);
    std::filesystem::rename(temp_path, output_path);

    result.output_generated = true;
    result.changes_applied = true;

    for (const auto& finding : findings) {
        if (finding.is_blocking() && finding.fixability == domain::Fixability::NONE) {
            result.records.push_back({
                "NoAutomaticFix",
                finding.code,
                false,
                false,
                "skipped",
                "Finding permanece sem correcao automatica segura.",
                {}});
        }
    }

    return result;
}

std::unique_ptr<FixEngine> create_default_fix_engine() {
    auto engine = std::make_unique<FixEngine>();
    engine->register_fix(std::make_unique<NormalizeBoxesFix>());
    engine->register_fix(std::make_unique<ConvertRgbToCmykFix>());
    engine->register_fix(std::make_unique<ImageColorConvertFix>());
    engine->register_fix(std::make_unique<AttachOutputIntentFix>());
    engine->register_fix(std::make_unique<TacReductionFix>());
    engine->register_fix(std::make_unique<BlackNormalizationFix>());
    engine->register_fix(std::make_unique<RemoveWhiteOverprintFix>());
    engine->register_fix(std::make_unique<RemoveAnnotationsFix>());
    engine->register_fix(std::make_unique<FlattenLayersFix>());
    engine->register_fix(std::make_unique<SpotColorConversionFix>());
    engine->register_fix(std::make_unique<RotationFix>());
    return engine;
}

} // namespace printguard::fix

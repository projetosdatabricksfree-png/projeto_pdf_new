#include "printguard/fix/fix_engine.hpp"

#include "printguard/common/logging.hpp"
#include "printguard/fix/fixes/normalize_boxes_fix.hpp"
#include "printguard/fix/fixes/convert_rgb_to_cmyk_fix.hpp"
#include <algorithm>
#include <filesystem>
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

} // namespace

void FixEngine::register_fix(std::unique_ptr<IFix> fix) {
    m_fixes.push_back(std::move(fix));
}

FixPlan FixPlanner::build_plan(
    const std::vector<domain::Finding>& findings,
    const FixEngine& engine) const {
    FixPlan plan;
    std::set<std::string> dedupe;

    for (const auto& finding : findings) {
        if (finding.is_blocking()) {
            plan.unresolved_finding_codes.push_back(finding.code);
            plan.has_blocking_unresolved = true;
        }

        // Map finding code to fix via engine's registered fixes
        for (const auto& fix : engine.m_fixes) {
            if (fix->targets_finding_code() == finding.code) {
                auto fix_id = fix->id();
                if (dedupe.insert(fix_id).second) {
                    plan.actions.push_back(fix_id);
                }
                break;
            }
        }
    }

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
    return engine;
}

} // namespace printguard::fix

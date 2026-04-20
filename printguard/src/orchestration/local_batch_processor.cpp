#include "printguard/orchestration/local_batch_processor.hpp"

#include "printguard/common/crypto.hpp"
#include "printguard/common/logging.hpp"
#include "printguard/domain/job.hpp"
#include "printguard/pdf/pdf_loader.hpp"
#include "printguard/report/report_builder.hpp"
#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <limits>
#include <nlohmann/json.hpp>
#include <set>

namespace printguard::orchestration {

namespace {

std::vector<char> read_file_to_bytes(std::string const& path) {
    std::ifstream ifs(path, std::ios::binary | std::ios::ate);
    if (!ifs) {
        throw std::runtime_error("Nao foi possivel abrir o arquivo de entrada: " + path);
    }
    auto size = ifs.tellg();
    if (size < 0) {
        throw std::runtime_error("Nao foi possivel ler o tamanho do arquivo: " + path);
    }
    std::vector<char> buffer(static_cast<std::size_t>(size));
    ifs.seekg(0);
    ifs.read(buffer.data(), size);
    if (!ifs && size > 0) {
        throw std::runtime_error("Leitura incompleta do arquivo de entrada: " + path);
    }
    return buffer;
}

void write_text_file(std::string const& path, std::string const& content) {
    std::ofstream ofs(path, std::ios::binary);
    ofs << content;
}

void write_json_file(std::string const& path, nlohmann::json const& json) {
    write_text_file(path, json.dump(2));
}

void persist_reports(orchestration::FileProcessResult& result) {
    auto report_started = std::chrono::steady_clock::now();
    write_json_file(
        result.technical_report_path, report::ReportBuilder::build_technical_report(result));
    write_json_file(result.client_report_path, report::ReportBuilder::build_client_report(result));
    write_text_file(result.summary_path, report::ReportBuilder::build_summary_markdown(result));
    result.report_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                           std::chrono::steady_clock::now() - report_started)
                           .count();
}

std::string basename_without_extension(std::string const& path) {
    return std::filesystem::path(path).stem().string();
}

domain::RevalidationDelta build_delta(
    std::vector<domain::Finding> const& initial,
    std::vector<domain::Finding> const& postfix) {
    domain::RevalidationDelta delta;
    std::set<std::string> initial_codes;
    std::set<std::string> postfix_codes;

    for (auto const& finding : initial) {
        initial_codes.insert(finding.code);
    }
    for (auto const& finding : postfix) {
        postfix_codes.insert(finding.code);
    }

    for (auto const& code : initial_codes) {
        if (!postfix_codes.contains(code)) {
            delta.resolved_codes.push_back(code);
        } else {
            delta.remaining_codes.push_back(code);
        }
    }
    for (auto const& code : postfix_codes) {
        if (!initial_codes.contains(code)) {
            delta.introduced_codes.push_back(code);
        }
    }

    return delta;
}

bool has_blocking_findings(std::vector<domain::Finding> const& findings) {
    return std::any_of(findings.begin(), findings.end(), [](auto const& finding) {
        return finding.is_blocking();
    });
}

std::string derive_final_status(
    bool has_blocking_remanescente,
    bool needs_manual_review,
    std::vector<std::string> const& manual_review_reasons) {
    if (has_blocking_remanescente &&
        (needs_manual_review || !manual_review_reasons.empty())) {
        return "manual_review_required";
    }
    return "completed";
}

} // namespace

LocalBatchProcessor::LocalBatchProcessor(
    std::map<std::string, domain::ProductPreset> presets,
    std::map<std::string, domain::ValidationProfile> profiles) :
    m_presets(std::move(presets)),
    m_profiles(std::move(profiles)),
    m_rule_engine(analysis::create_default_engine()),
    m_fix_engine(fix::create_default_fix_engine()) {
}

BatchProcessSummary LocalBatchProcessor::process_directory(
    const std::string& input_dir,
    const std::string& corrected_dir,
    const std::string& report_dir,
    const std::string& preferred_preset_id,
    const std::string& profile_id) {
    BatchProcessSummary summary;

    std::filesystem::create_directories(corrected_dir);
    std::filesystem::create_directories(report_dir);

    std::vector<std::filesystem::path> pdfs;
    for (auto const& entry : std::filesystem::directory_iterator(input_dir)) {
        if (entry.is_regular_file() && entry.path().extension() == ".pdf") {
            pdfs.push_back(entry.path());
        }
    }
    std::sort(pdfs.begin(), pdfs.end());

    for (auto const& pdf : pdfs) {
        auto file_result =
            process_file(pdf.string(), corrected_dir, report_dir, preferred_preset_id, profile_id);
        summary.files.push_back(file_result);
    }

    summary.total_files = static_cast<int>(summary.files.size());
    for (auto const& file : summary.files) {
        if (file.final_status == "completed") {
            ++summary.completed_files;
        } else if (file.final_status == "manual_review_required") {
            ++summary.manual_review_files;
        } else {
            ++summary.failed_files;
        }
    }

    summary.batch_report_json_path =
        (std::filesystem::path(report_dir) / "relatorio_lote.json").string();
    summary.batch_report_markdown_path =
        (std::filesystem::path(report_dir) / "relatorio_lote.md").string();

    write_json_file(summary.batch_report_json_path, report::ReportBuilder::build_batch_report(summary));
    write_text_file(summary.batch_report_markdown_path, report::ReportBuilder::build_batch_markdown(summary));

    return summary;
}

FileProcessResult LocalBatchProcessor::process_file(
    const std::string& input_pdf,
    const std::string& corrected_dir,
    const std::string& report_dir,
    const std::string& preferred_preset_id,
    const std::string& profile_id) const {
    auto const& preset = select_preset(input_pdf, preferred_preset_id);
    auto const& profile = get_profile(profile_id);
    return process_file(input_pdf, corrected_dir, report_dir, preset, profile);
}

FileProcessResult LocalBatchProcessor::process_file(
    const std::string& input_pdf,
    const std::string& corrected_dir,
    const std::string& report_dir,
    const domain::ProductPreset& preset,
    const domain::ValidationProfile& profile,
    std::function<void(const std::string&)> stage_callback) const {
    FileProcessResult result;
    auto started_at = std::chrono::steady_clock::now();
    result.original_path = input_pdf;
    result.original_filename = std::filesystem::path(input_pdf).filename().string();
    result.profile_id = profile.id;
    result.preset_id = preset.id;
    result.preset_family = domain::product_family_to_string(preset.family);

    std::filesystem::path corrected_path =
        std::filesystem::path(corrected_dir) /
        (basename_without_extension(input_pdf) + "_corrigido.pdf");
    std::filesystem::path report_base =
        std::filesystem::path(report_dir) / basename_without_extension(input_pdf);
    result.corrected_path = corrected_path.string();
    result.technical_report_path = report_base.string() + "_relatorio_tecnico.json";
    result.client_report_path = report_base.string() + "_relatorio_cliente.json";
    result.summary_path = report_base.string() + "_resumo.md";

    try {
        auto bytes = read_file_to_bytes(input_pdf);
        result.checksum_sha256 = common::Crypto::sha256(bytes);

        if (stage_callback) {
            stage_callback(domain::JobStatusValue::ANALYZING);
        }
        auto analysis_started = std::chrono::steady_clock::now();
        auto initial = m_rule_engine->run(input_pdf, preset, profile);
        result.analysis_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                                 std::chrono::steady_clock::now() - analysis_started)
                                 .count();
        result.initial_findings = initial.findings;
        result.warnings.insert(result.warnings.end(), initial.warnings.begin(), initial.warnings.end());

        if (stage_callback) {
            stage_callback(domain::JobStatusValue::FIXING);
        }
        auto fix_started = std::chrono::steady_clock::now();
        auto fix_plan = m_fix_planner.build_plan(result.initial_findings, *m_fix_engine, preset);
        result.planner_status = fix_plan.status;
        result.fixes_not_applied = fix_plan.unresolved_finding_codes;
        result.skipped_fixes = fix_plan.skipped_fixes;
        result.manual_review_reasons = fix_plan.manual_review_reasons;
        result.needs_manual_review = fix_plan.needs_manual_review;
        result.has_blocking_unresolved = fix_plan.has_blocking_unresolved;
        result.fixes_not_applied = fix_plan.unresolved_finding_codes;
        result.correction_attempted = !fix_plan.actions.empty();
        auto fix_result =
            m_fix_engine->execute(input_pdf, corrected_path.string(), fix_plan, result.initial_findings, preset);
        result.fix_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                            std::chrono::steady_clock::now() - fix_started)
                            .count();
        result.fixes_applied = fix_result.records;
        result.correction_applied = fix_result.changes_applied;
        result.corrected_is_passthrough = !fix_result.changes_applied;

        if (stage_callback) {
            stage_callback(domain::JobStatusValue::REVALIDATING);
        }
        auto revalidation_started = std::chrono::steady_clock::now();
        auto postfix = m_rule_engine->run(result.corrected_path, preset, profile);
        result.revalidation_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                                     std::chrono::steady_clock::now() - revalidation_started)
                                     .count();
        result.postfix_findings = postfix.findings;
        result.revalidation = build_delta(result.initial_findings, result.postfix_findings);
        result.warnings.insert(result.warnings.end(), postfix.warnings.begin(), postfix.warnings.end());

        auto preview_started = std::chrono::steady_clock::now();
        auto preview = m_preview_renderer.render_first_page(
            result.corrected_path, (report_base.string() + "_preview_p0.png"));
        result.preview_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                                std::chrono::steady_clock::now() - preview_started)
                                .count();
        result.preview_path = preview.output_path;
        result.preview_generated = preview.generated;
        if (!preview.generated && !preview.warning.empty()) {
            result.warnings.push_back(preview.warning);
        }

        result.has_blocking_unresolved = has_blocking_findings(result.postfix_findings);
        result.final_status = derive_final_status(
            result.has_blocking_unresolved, result.needs_manual_review, result.manual_review_reasons);

        persist_reports(result);
    } catch (const std::exception& e) {
        result.final_status = "failed";
        result.errors.push_back(e.what());
    }

    result.total_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                          std::chrono::steady_clock::now() - started_at)
                          .count();

    if (result.final_status == "failed") {
        try {
            persist_reports(result);
        } catch (const std::exception& e) {
            result.errors.push_back(std::string("Falha ao gerar relatorios: ") + e.what());
            result.report_ms = 0;
        }
    }

    return result;
}

const domain::ProductPreset& LocalBatchProcessor::select_preset(
    const std::string& input_pdf,
    const std::string& preferred_preset_id) const {
    if (!preferred_preset_id.empty() && preferred_preset_id != "auto") {
        return m_presets.at(preferred_preset_id);
    }

    auto model = pdf::PdfLoader::load_from_file(input_pdf);
    if (!model.pages.empty()) {
        auto const& first_page = model.pages.front();
        double best_score = std::numeric_limits<double>::max();
        domain::ProductPreset const* best_match = nullptr;

        for (auto const& [id, preset] : m_presets) {
            double direct_score =
                std::abs(first_page.trim_box.w - preset.final_width_mm) +
                std::abs(first_page.trim_box.h - preset.final_height_mm);
            double rotated_score =
                std::abs(first_page.trim_box.w - preset.final_height_mm) +
                std::abs(first_page.trim_box.h - preset.final_width_mm);
            double score = std::min(direct_score, rotated_score);
            if (score < best_score) {
                best_score = score;
                best_match = &preset;
            }
        }

        if (best_match != nullptr) {
            return *best_match;
        }
    }

    return m_presets.begin()->second;
}

const domain::ValidationProfile& LocalBatchProcessor::get_profile(const std::string& profile_id) const {
    return m_profiles.at(profile_id);
}

} // namespace printguard::orchestration

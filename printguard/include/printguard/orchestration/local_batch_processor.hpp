#pragma once

#include "printguard/analysis/rule_engine.hpp"
#include "printguard/domain/config_loader.hpp"
#include "printguard/domain/finding.hpp"
#include "printguard/fix/fix_engine.hpp"
#include "printguard/render/preview_renderer.hpp"
#include <functional>
#include <map>
#include <string>
#include <vector>

namespace printguard::orchestration {

struct FileProcessResult {
    std::string original_filename;
    std::string original_path;
    std::string checksum_sha256;
    std::string preset_id;
    std::string profile_id;
    std::string preset_family;
    std::vector<domain::Finding> initial_findings;
    std::vector<domain::Finding> postfix_findings;
    std::vector<domain::FixRecord> fixes_applied;
    std::vector<std::string> fixes_not_applied;
    std::vector<std::string> skipped_fixes;
    domain::RevalidationDelta revalidation;
    std::string final_status;
    std::string planner_status;
    std::string corrected_path;
    std::string preview_path;
    std::string technical_report_path;
    std::string client_report_path;
    std::string summary_path;
    bool correction_attempted = false;
    bool correction_applied = false;
    bool corrected_is_passthrough = false;
    bool needs_manual_review = false;
    bool has_blocking_unresolved = false;
    bool preview_generated = false;
    long long analysis_ms = 0;
    long long fix_ms = 0;
    long long revalidation_ms = 0;
    long long preview_ms = 0;
    long long report_ms = 0;
    long long total_ms = 0;
    std::vector<std::string> manual_review_reasons;
    std::vector<std::string> warnings;
    std::vector<std::string> errors;
};

struct BatchProcessSummary {
    std::vector<FileProcessResult> files;
    std::string batch_report_markdown_path;
    std::string batch_report_json_path;
    int total_files = 0;
    int completed_files = 0;
    int manual_review_files = 0;
    int failed_files = 0;
};

class LocalBatchProcessor {
public:
    LocalBatchProcessor(
        std::map<std::string, domain::ProductPreset> presets,
        std::map<std::string, domain::ValidationProfile> profiles);

    BatchProcessSummary process_directory(
        const std::string& input_dir,
        const std::string& corrected_dir,
        const std::string& report_dir,
        const std::string& preferred_preset_id,
        const std::string& profile_id);

    FileProcessResult process_file(
        const std::string& input_pdf,
        const std::string& corrected_dir,
        const std::string& report_dir,
        const domain::ProductPreset& preset,
        const domain::ValidationProfile& profile,
        std::function<void(const std::string&)> stage_callback = {}) const;

private:
    FileProcessResult process_file(
        const std::string& input_pdf,
        const std::string& corrected_dir,
        const std::string& report_dir,
        const std::string& preferred_preset_id,
        const std::string& profile_id) const;

    const domain::ProductPreset& select_preset(
        const std::string& input_pdf,
        const std::string& preferred_preset_id) const;

    const domain::ValidationProfile& get_profile(const std::string& profile_id) const;

    std::map<std::string, domain::ProductPreset> m_presets;
    std::map<std::string, domain::ValidationProfile> m_profiles;
    std::unique_ptr<analysis::RuleEngine> m_rule_engine;
    fix::FixPlanner m_fix_planner;
    std::unique_ptr<fix::FixEngine> m_fix_engine;
    render::PreviewRenderer m_preview_renderer;
};

} // namespace printguard::orchestration

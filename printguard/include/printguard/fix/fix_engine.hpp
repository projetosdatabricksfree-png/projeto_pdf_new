#pragma once

#include "printguard/domain/finding.hpp"
#include "printguard/domain/preset.hpp"
#include "printguard/fix/fix_interface.hpp"
#include <memory>
#include <string>
#include <vector>

namespace printguard::fix {

class FixEngine;

struct FixPlan {
    std::vector<std::string> actions;
    std::vector<std::string> skipped_fixes;
    std::vector<std::string> unresolved_finding_codes;
    bool needs_manual_review = false;
    std::vector<std::string> manual_review_reasons;
    bool has_blocking_unresolved = false;
    std::string status = "completed";
};

struct FixExecutionResult {
    std::vector<domain::FixRecord> records;
    bool output_generated = false;
    bool changes_applied = false;
    std::string output_path;
};

class FixPlanner {
public:
    FixPlan build_plan(
        const std::vector<domain::Finding>& findings,
        const FixEngine& engine,
        const domain::ProductPreset& preset) const;
};

class FixEngine {
public:
    void register_fix(std::unique_ptr<IFix> fix);

    FixExecutionResult execute(
        const std::string& input_pdf,
        const std::string& output_pdf,
        const FixPlan& plan,
        const std::vector<domain::Finding>& findings,
        const domain::ProductPreset& preset) const;

private:
    friend class FixPlanner;
    std::vector<std::unique_ptr<IFix>> m_fixes;
};

std::unique_ptr<FixEngine> create_default_fix_engine();

} // namespace printguard::fix

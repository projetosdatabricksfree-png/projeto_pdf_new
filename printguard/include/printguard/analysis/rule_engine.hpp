#pragma once

#include "printguard/analysis/rule_interface.hpp"
#include "printguard/domain/finding.hpp"
#include "printguard/domain/preset.hpp"
#include "printguard/domain/profile.hpp"
#include "printguard/pdf/canonical_model.hpp"
#include <memory>
#include <string>
#include <vector>

namespace printguard::analysis {

struct AnalysisResult {
    pdf::DocumentModel document;
    std::vector<domain::Finding> findings;
    std::vector<std::string> warnings;
};

class RuleEngine {
public:
    void register_rule(std::unique_ptr<IRule> rule);

    AnalysisResult run(
        const std::string& pdf_path,
        const domain::ProductPreset& preset,
        const domain::ValidationProfile& profile) const;

private:
    std::vector<std::unique_ptr<IRule>> m_rules;
};

std::unique_ptr<RuleEngine> create_default_engine();

} // namespace printguard::analysis

#pragma once

#include "printguard/analysis/rule_interface.hpp"

namespace printguard::analysis {

class LayerRule : public IRule {
public:
    std::string id() const override;
    std::string category() const override;
    std::vector<domain::Finding> evaluate(const RuleContext& ctx) const override;
};

} // namespace printguard::analysis

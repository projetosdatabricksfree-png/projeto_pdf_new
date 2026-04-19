#pragma once

#include "printguard/domain/finding.hpp"
#include "printguard/domain/preset.hpp"
#include "printguard/domain/profile.hpp"
#include "printguard/pdf/canonical_model.hpp"
#include <qpdf/QPDF.hh>
#include <string>
#include <vector>

namespace printguard::analysis {

struct RuleContext {
    QPDF& pdf;
    const pdf::DocumentModel& document;
    const domain::ProductPreset& preset;
    const domain::ValidationProfile& profile;
};

class IRule {
public:
    virtual ~IRule() = default;
    virtual std::string id() const = 0;
    virtual std::string category() const = 0;
    virtual std::vector<domain::Finding> evaluate(const RuleContext& ctx) const = 0;
};

} // namespace printguard::analysis

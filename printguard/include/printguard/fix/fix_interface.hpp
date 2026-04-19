#pragma once

#include "printguard/domain/finding.hpp"
#include "printguard/domain/preset.hpp"
#include <qpdf/QPDF.hh>
#include <string>
#include <vector>

namespace printguard::fix {

struct FixContext {
    QPDF& pdf;
    const domain::ProductPreset& preset;
    const std::vector<domain::Finding>& findings;
};

class IFix {
public:
    virtual ~IFix() = default;
    virtual std::string id() const = 0;
    virtual std::string targets_finding_code() const = 0;
    virtual domain::FixRecord apply(FixContext& ctx) const = 0;
};

} // namespace printguard::fix

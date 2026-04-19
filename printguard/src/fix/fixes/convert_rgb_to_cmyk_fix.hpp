#pragma once

#include "printguard/fix/fix_interface.hpp"

namespace printguard::fix {

class ConvertRgbToCmykFix : public IFix {
public:
    std::string id() const override;
    std::string targets_finding_code() const override;
    domain::FixRecord apply(FixContext& ctx) const override;
};

} // namespace printguard::fix

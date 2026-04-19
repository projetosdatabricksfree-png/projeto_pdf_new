#pragma once

#include <string>
#include <map>

namespace printguard::domain {

enum class RuleSeverity {
    INFO,
    WARNING,
    ERROR
};

struct RuleConfig {
    bool enabled;
    RuleSeverity severity;
    std::map<std::string, std::string> params;
};

struct ValidationProfile {
    std::string id;
    std::string name;
    std::string description;
    std::map<std::string, RuleConfig> rules;
};

} // namespace printguard::domain

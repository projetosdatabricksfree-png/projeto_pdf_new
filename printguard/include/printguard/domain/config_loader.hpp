#pragma once

#include "printguard/domain/preset.hpp"
#include "printguard/domain/profile.hpp"
#include <map>
#include <string>
#include <memory>

namespace printguard::domain {

class ConfigLoader {
public:
    static std::map<std::string, ProductPreset> load_presets(const std::string& path);
    static std::map<std::string, ValidationProfile> load_profiles(const std::string& path);

private:
    static RuleSeverity severity_from_string(const std::string& s);
};

} // namespace printguard::domain

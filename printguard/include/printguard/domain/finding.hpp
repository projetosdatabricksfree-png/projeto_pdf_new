#pragma once

#include <map>
#include <string>
#include <vector>

namespace printguard::domain {

enum class FindingSeverity {
    INFO,
    WARNING,
    ERROR
};

enum class Fixability {
    NONE,
    AUTOMATIC_SAFE,
    AUTOMATIC_RISKY
};

struct Finding {
    std::string code;
    std::string rule_id;
    std::string category;
    FindingSeverity severity = FindingSeverity::WARNING;
    Fixability fixability = Fixability::NONE;
    int page_number = 0;
    std::string technical_message;
    std::string user_message;
    std::map<std::string, std::string> evidence;

    [[nodiscard]] bool is_blocking() const;
};

struct FixRecord {
    std::string fix_id;
    std::string finding_code;
    bool attempted = false;
    bool success = false;
    std::string status;
    std::string message;
    std::map<std::string, std::string> details;
};

struct RevalidationDelta {
    std::vector<std::string> resolved_codes;
    std::vector<std::string> remaining_codes;
    std::vector<std::string> introduced_codes;
};

std::string to_string(FindingSeverity severity);
std::string to_string(Fixability fixability);

} // namespace printguard::domain

#pragma once

#include <string>
#include <vector>
#include <stdexcept>

namespace printguard::domain {

enum class JobStatus {
    UPLOADED,
    QUEUED,
    PARSING,
    ANALYZING,
    FIXING,
    REVALIDATING,
    COMPLETED,
    FAILED
};

class JobStateMachine {
public:
    static std::string status_to_string(JobStatus status);
    static JobStatus string_to_status(const std::string& status);
    
    static bool can_transition(JobStatus from, JobStatus to);
};

} // namespace printguard::domain

#include "printguard/domain/state_machine.hpp"
#include <map>

namespace printguard::domain {

std::string JobStateMachine::status_to_string(JobStatus status) {
    switch (status) {
        case JobStatus::UPLOADED: return "uploaded";
        case JobStatus::QUEUED: return "queued";
        case JobStatus::PARSING: return "parsing";
        case JobStatus::ANALYZING: return "analyzing";
        case JobStatus::FIXING: return "fixing";
        case JobStatus::REVALIDATING: return "revalidating";
        case JobStatus::COMPLETED: return "completed";
        case JobStatus::FAILED: return "failed";
    }
    return "unknown";
}

JobStatus JobStateMachine::string_to_status(const std::string& status) {
    if (status == "uploaded") return JobStatus::UPLOADED;
    if (status == "queued") return JobStatus::QUEUED;
    if (status == "parsing") return JobStatus::PARSING;
    if (status == "analyzing") return JobStatus::ANALYZING;
    if (status == "fixing") return JobStatus::FIXING;
    if (status == "revalidating") return JobStatus::REVALIDATING;
    if (status == "completed") return JobStatus::COMPLETED;
    if (status == "failed") return JobStatus::FAILED;
    throw std::runtime_error("Unknown status: " + status);
}

bool JobStateMachine::can_transition(JobStatus from, JobStatus to) {
    if (to == JobStatus::FAILED) return true; // Can always fail
    
    switch (from) {
        case JobStatus::UPLOADED:
            return to == JobStatus::QUEUED;
        case JobStatus::QUEUED:
            return to == JobStatus::PARSING;
        case JobStatus::PARSING:
            return to == JobStatus::ANALYZING;
        case JobStatus::ANALYZING:
            return to == JobStatus::FIXING || to == JobStatus::COMPLETED;
        case JobStatus::FIXING:
            return to == JobStatus::REVALIDATING;
        case JobStatus::REVALIDATING:
            return to == JobStatus::COMPLETED;
        case JobStatus::COMPLETED:
        case JobStatus::FAILED:
            return false; // Final states
    }
    return false;
}

} // namespace printguard::domain

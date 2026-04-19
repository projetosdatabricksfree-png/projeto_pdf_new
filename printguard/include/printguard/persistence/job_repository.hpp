#pragma once

#include "printguard/domain/job.hpp"
#include <string>
#include <vector>
#include <optional>

namespace printguard::persistence {

class JobRepository {
public:
    static std::string create(const std::string& tenant_id, const std::string& filename, 
                             const std::string& preset_id, const std::string& profile_id);
    static void update_status(const std::string& job_id, const std::string& status);
    static std::optional<domain::Job> get_by_id(const std::string& job_id);
    
    // Queue Ops
    static std::optional<std::string> claim_next_job(const std::string& from_status, const std::string& to_status);
    
    // Artifacts
    static void add_artifact(const domain::Artifact& artifact);
    static std::vector<domain::Artifact> get_artifacts(const std::string& job_id);
};

} // namespace printguard::persistence

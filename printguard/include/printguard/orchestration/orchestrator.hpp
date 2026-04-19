#pragma once

#include "printguard/storage/storage.hpp"
#include "printguard/domain/preset.hpp"
#include "printguard/domain/profile.hpp"
#include <string>
#include <vector>
#include <memory>

namespace printguard::orchestration {

struct JobUploadResult {
    std::string job_id;
    bool success;
    std::string error_message;
};

class JobOrchestrator {
public:
    JobOrchestrator(storage::IStorage& storage);
    
    JobUploadResult process_upload(
        const std::string& tenant_id,
        const std::string& filename,
        const std::vector<char>& data,
        const std::string& preset_id,
        const std::string& profile_id
    );

    bool run_pipeline(const std::string& job_id);

private:
    storage::IStorage& m_storage;
};

} // namespace printguard::orchestration

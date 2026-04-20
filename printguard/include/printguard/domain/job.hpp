#pragma once
#include <string>
#include <vector>
#include <chrono>

namespace printguard::domain {

struct JobStatusValue {
    static constexpr const char* UPLOADED = "uploaded";
    static constexpr const char* PROCESSING = "processing";
    static constexpr const char* ANALYZING = "analyzing";
    static constexpr const char* FIXING = "fixing";
    static constexpr const char* REVALIDATING = "revalidating";
    static constexpr const char* MANUAL_REVIEW_REQUIRED = "manual_review_required";
    static constexpr const char* COMPLETED = "completed";
    static constexpr const char* FAILED = "failed";
};

struct Job {
    std::string id;
    std::string tenant_id;
    std::string status;
    std::string original_filename;
    std::string preset_id;
    std::string profile_id;
    std::string created_at;
    std::string updated_at;
};

struct Artifact {
    std::string id;
    std::string job_id;
    std::string type;
    std::string path;
    long long file_size;
    std::string checksum_sha256;
};

} // namespace printguard::domain

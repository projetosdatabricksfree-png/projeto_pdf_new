#include "printguard/orchestration/orchestrator.hpp"
#include "printguard/persistence/job_repository.hpp"
#include "printguard/pdf/pdf_loader.hpp"
#include "printguard/common/logging.hpp"
#include "printguard/common/crypto.hpp"
#include "printguard/domain/job.hpp"
#include <exception>
#include <algorithm>

namespace printguard::orchestration {

JobOrchestrator::JobOrchestrator(storage::IStorage& storage) : m_storage(storage) {}

JobUploadResult JobOrchestrator::process_upload(
    const std::string& tenant_id,
    const std::string& filename,
    const std::vector<char>& data,
    const std::string& preset_id,
    const std::string& profile_id
) {
    JobUploadResult result;
    result.success = false;

    // 1. Validation
    if (!common::Crypto::is_pdf(data)) {
        result.error_message = "Invalid PDF signature";
        return result;
    }

    try {
        // 2. Database Registration
        result.job_id = persistence::JobRepository::create(tenant_id, filename, preset_id, profile_id);
        
        // 3. Physical Storage
        std::string path = m_storage.put(result.job_id, tenant_id, "original", data);

        // 4. Artifact Registration
        domain::Artifact art;
        art.job_id = result.job_id;
        art.type = "original";
        art.path = path;
        art.file_size = data.size();
        art.checksum_sha256 = common::Crypto::sha256(data);
        
        persistence::JobRepository::add_artifact(art);

        result.success = true;
        PG_LOG_INFO("Job {} successfully orchestrated/uploaded", result.job_id);

    } catch (const std::exception& e) {
        result.error_message = e.what();
        PG_LOG_ERROR("Upload orchestration failed for job: {}", e.what());
    }

    return result;
}

bool JobOrchestrator::run_pipeline(const std::string& job_id) {
    PG_LOG_INFO("Running pipeline for job {}", job_id);
    
    try {
        // 1. Get Artifacts
        auto artifacts = persistence::JobRepository::get_artifacts(job_id);
        auto it = std::find_if(artifacts.begin(), artifacts.end(), [](const auto& a) {
            return a.type == "original";
        });

        if (it == artifacts.end()) {
            PG_LOG_ERROR("Job {} has no 'original' artifact", job_id);
            persistence::JobRepository::update_status(job_id, domain::JobStatusValue::FAILED);
            return false;
        }

        // 2. Read from Storage
        std::vector<char> data = m_storage.get(it->path);
        if (data.empty()) {
            PG_LOG_ERROR("Failed to read data for job {} at path {}", job_id, it->path);
            persistence::JobRepository::update_status(job_id, domain::JobStatusValue::FAILED);
            return false;
        }

        // 3. Parsing Step (Extracting PDF metadata/metrics)
        auto pdf_model = pdf::PdfLoader::load_from_memory(data);
        PG_LOG_INFO("Job {}: PDF Parsed ({} pages)", job_id, pdf_model.page_count);

        // 4. Update Status to ANALYZING (Ready for Preflight Rules in Sprint 06)
        persistence::JobRepository::update_status(job_id, domain::JobStatusValue::ANALYZING);

        return true;

    } catch (const std::exception& e) {
        PG_LOG_ERROR("Pipeline failed for job {}: {}", job_id, e.what());
        persistence::JobRepository::update_status(job_id, domain::JobStatusValue::FAILED);
        return false;
    }
}

} // namespace printguard::orchestration

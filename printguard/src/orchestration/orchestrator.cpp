#include "printguard/orchestration/orchestrator.hpp"
#include "printguard/common/logging.hpp"
#include "printguard/common/crypto.hpp"
#include "printguard/domain/job.hpp"
#include "printguard/pdf/pdf_loader.hpp"
#include "printguard/persistence/job_repository.hpp"
#include <filesystem>
#include <fstream>
#include <exception>
#include <algorithm>

namespace printguard::orchestration {

namespace {

std::vector<char> read_file_bytes(std::string const& path) {
    std::ifstream ifs(path, std::ios::binary | std::ios::ate);
    if (!ifs) {
        throw std::runtime_error("Nao foi possivel abrir artefato para persistencia: " + path);
    }
    auto size = ifs.tellg();
    std::vector<char> buffer(static_cast<std::size_t>(size));
    ifs.seekg(0);
    ifs.read(buffer.data(), size);
    return buffer;
}

void write_file_bytes(std::filesystem::path const& path, std::vector<char> const& data) {
    std::filesystem::create_directories(path.parent_path());
    std::ofstream ofs(path, std::ios::binary);
    if (!ofs) {
        throw std::runtime_error("Nao foi possivel escrever arquivo temporario: " + path.string());
    }
    ofs.write(data.data(), static_cast<std::streamsize>(data.size()));
}

void persist_artifact(
    storage::IStorage& storage,
    std::string const& tenant_id,
    std::string const& job_id,
    std::string const& type,
    std::vector<char> const& data) {
    auto path = storage.put(job_id, tenant_id, type, data);
    domain::Artifact artifact;
    artifact.job_id = job_id;
    artifact.type = type;
    artifact.path = path;
    artifact.file_size = static_cast<long long>(data.size());
    artifact.checksum_sha256 = common::Crypto::sha256(data);
    persistence::JobRepository::add_artifact(artifact);
}

void persist_artifact_from_path(
    storage::IStorage& storage,
    std::string const& tenant_id,
    std::string const& job_id,
    std::string const& type,
    std::string const& path) {
    persist_artifact(storage, tenant_id, job_id, type, read_file_bytes(path));
}

} // namespace

JobOrchestrator::JobOrchestrator(
    storage::IStorage& storage,
    std::map<std::string, domain::ProductPreset> presets,
    std::map<std::string, domain::ValidationProfile> profiles) :
    m_storage(storage),
    m_presets(std::move(presets)),
    m_profiles(std::move(profiles)),
    m_batch_processor(m_presets, m_profiles) {
}

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
        auto job = persistence::JobRepository::get_by_id(job_id);
        if (!job) {
            PG_LOG_ERROR("Job {} not found", job_id);
            persistence::JobRepository::update_status(job_id, domain::JobStatusValue::FAILED);
            return false;
        }

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

        auto preset_it = m_presets.find(job->preset_id);
        if (preset_it == m_presets.end()) {
            PG_LOG_ERROR("Job {} preset {} not found", job_id, job->preset_id);
            persistence::JobRepository::update_status(job_id, domain::JobStatusValue::FAILED);
            return false;
        }

        auto profile_it = m_profiles.find(job->profile_id);
        if (profile_it == m_profiles.end()) {
            PG_LOG_ERROR("Job {} profile {} not found", job_id, job->profile_id);
            persistence::JobRepository::update_status(job_id, domain::JobStatusValue::FAILED);
            return false;
        }

        persistence::JobRepository::update_status(job_id, domain::JobStatusValue::PROCESSING);

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

        std::filesystem::path workspace =
            std::filesystem::temp_directory_path() / "printguard_job_pipeline" / job_id;
        std::filesystem::path input_dir = workspace / "input";
        std::filesystem::path corrected_dir = workspace / "corrected";
        std::filesystem::path report_dir = workspace / "reports";
        std::filesystem::path input_pdf = input_dir / job->original_filename;
        write_file_bytes(input_pdf, data);

        auto result = m_batch_processor.process_file(
            input_pdf.string(),
            corrected_dir.string(),
            report_dir.string(),
            preset_it->second,
            profile_it->second,
            [&](const std::string& stage) {
                persistence::JobRepository::update_status(job_id, stage);
            });

        persist_artifact_from_path(
            m_storage, job->tenant_id, job_id, "corrected_pdf", result.corrected_path);
        persist_artifact_from_path(
            m_storage, job->tenant_id, job_id, "technical_report", result.technical_report_path);
        persist_artifact_from_path(
            m_storage, job->tenant_id, job_id, "client_report", result.client_report_path);
        persist_artifact_from_path(
            m_storage, job->tenant_id, job_id, "summary_report", result.summary_path);

        if (result.preview_generated && !result.preview_path.empty()) {
            try {
                persist_artifact_from_path(
                    m_storage, job->tenant_id, job_id, "preview_png", result.preview_path);
            } catch (const std::exception& e) {
                PG_LOG_WARN("Job {} preview persistence failed: {}", job_id, e.what());
            }
        }

        std::string final_status = domain::JobStatusValue::FAILED;
        if (result.final_status == domain::JobStatusValue::COMPLETED) {
            final_status = domain::JobStatusValue::COMPLETED;
        } else if (result.final_status == domain::JobStatusValue::MANUAL_REVIEW_REQUIRED) {
            final_status = domain::JobStatusValue::MANUAL_REVIEW_REQUIRED;
        }
        persistence::JobRepository::update_status(job_id, final_status);

        return final_status != domain::JobStatusValue::FAILED;

    } catch (const std::exception& e) {
        PG_LOG_ERROR("Pipeline failed for job {}: {}", job_id, e.what());
        persistence::JobRepository::update_status(job_id, domain::JobStatusValue::FAILED);
        return false;
    }
}

} // namespace printguard::orchestration

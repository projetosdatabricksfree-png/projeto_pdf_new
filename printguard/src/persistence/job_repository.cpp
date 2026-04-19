#include "printguard/persistence/job_repository.hpp"
#include "printguard/persistence/database.hpp"
#include "printguard/common/logging.hpp"

namespace printguard::persistence {

std::string JobRepository::create(const std::string& tenant_id, const std::string& filename,
                               const std::string& preset_id, const std::string& profile_id) {
    auto& conn = Database::get_connection();
    pqxx::work w(conn);
    
    pqxx::result r = w.exec_params(
        "INSERT INTO jobs (tenant_id, status, original_filename, preset_id, profile_id) VALUES ($1, $2, $3, $4, $5) RETURNING id",
        tenant_id, domain::JobStatusValue::UPLOADED, filename, preset_id, profile_id
    );
    
    w.commit();
    return r[0]["id"].as<std::string>();
}

void JobRepository::update_status(const std::string& job_id, const std::string& status) {
    auto& conn = Database::get_connection();
    pqxx::work w(conn);
    w.exec_params("UPDATE jobs SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2", status, job_id);
    w.commit();
}

std::optional<domain::Job> JobRepository::get_by_id(const std::string& job_id) {
    auto& conn = Database::get_connection();
    pqxx::read_transaction w(conn);
    pqxx::result r = w.exec_params("SELECT id, tenant_id, status, original_filename, preset_id, profile_id FROM jobs WHERE id = $1", job_id);
    
    if (r.empty()) return std::nullopt;
    
    domain::Job job;
    job.id = r[0]["id"].as<std::string>();
    job.tenant_id = r[0]["tenant_id"].as<std::string>();
    job.status = r[0]["status"].as<std::string>();
    job.original_filename = r[0]["original_filename"].as<std::string>();
    job.preset_id = r[0]["preset_id"].as<std::string>();
    job.profile_id = r[0]["profile_id"].as<std::string>();
    return job;
}

std::optional<std::string> JobRepository::claim_next_job(const std::string& from_status, const std::string& to_status) {
    auto& conn = Database::get_connection();
    pqxx::work w(conn);
    
    // Atomically find, lock and update the next available job
    pqxx::result r = w.exec_params(
        "UPDATE jobs SET status = $1, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = (SELECT id FROM jobs WHERE status = $2 ORDER BY created_at ASC LIMIT 1 FOR UPDATE SKIP LOCKED) "
        "RETURNING id",
        to_status, from_status
    );
    
    if (r.empty()) return std::nullopt;
    
    w.commit();
    return r[0]["id"].as<std::string>();
}

void JobRepository::add_artifact(const domain::Artifact& artifact) {
    auto& conn = Database::get_connection();
    pqxx::work w(conn);
    w.exec_params(
        "INSERT INTO artifacts (job_id, type, path, file_size, checksum_sha256) VALUES ($1, $2, $3, $4, $5)",
        artifact.job_id, artifact.type, artifact.path, artifact.file_size, artifact.checksum_sha256
    );
    w.commit();
}

std::vector<domain::Artifact> JobRepository::get_artifacts(const std::string& job_id) {
    auto& conn = Database::get_connection();
    pqxx::read_transaction w(conn);
    pqxx::result r = w.exec_params("SELECT id, job_id, type, path, file_size, checksum_sha256 FROM artifacts WHERE job_id = $1", job_id);
    
    std::vector<domain::Artifact> artifacts;
    for (auto const& row : r) {
        domain::Artifact art;
        art.id = row["id"].as<std::string>();
        art.job_id = row["job_id"].as<std::string>();
        art.type = row["type"].as<std::string>();
        art.path = row["path"].as<std::string>();
        art.file_size = row["file_size"].as<long long>();
        art.checksum_sha256 = row["checksum_sha256"].as<std::string>();
        artifacts.push_back(art);
    }
    return artifacts;
}

} // namespace printguard::persistence

#include "printguard/common/logging.hpp"
#include "printguard/common/env.hpp"
#include "printguard/persistence/database.hpp"
#include "printguard/persistence/job_repository.hpp"
#include "printguard/storage/storage.hpp"
#include "printguard/orchestration/orchestrator.hpp"
#include "printguard/domain/job.hpp"
#include <iostream>
#include <chrono>
#include <thread>
#include <csignal>
#include <atomic>

using namespace printguard;

std::atomic<bool> g_running{true};

void signal_handler(int) {
    PG_LOG_INFO("Shutdown signal received. Stopping worker...");
    g_running = false;
}

int main() {
    common::Logger::init("printguard-worker");
    PG_LOG_INFO("PrintGuard Worker starting...");

    std::signal(SIGINT, signal_handler);
    std::signal(SIGTERM, signal_handler);

    try {
        // 1. Initializations
        persistence::Database::init(common::Env::get("PG_CONN_STR"));
        storage::LocalStorage store(common::Env::get("STORAGE_ROOT", "./storage_data"));
        orchestration::JobOrchestrator orchestrator(store);

        PG_LOG_INFO("Worker entering main loop...");

        while (g_running) {
            // 2. Claim next available job
            auto job_id = persistence::JobRepository::claim_next_job(
                domain::JobStatusValue::UPLOADED, 
                domain::JobStatusValue::PROCESSING
            );

            if (job_id) {
                PG_LOG_INFO("Claimed job {}. Starting pipeline...", *job_id);
                
                bool result = orchestrator.run_pipeline(*job_id);
                
                if (result) {
                    PG_LOG_INFO("Job {} pipeline finished successfully", *job_id);
                } else {
                    PG_LOG_ERROR("Job {} pipeline failed", *job_id);
                }
                
                // Continue immediately to next job
                continue; 
            }

            // 3. Backoff if no jobs found
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
        }

    } catch (const std::exception& e) {
        PG_LOG_CRITICAL("Worker crashed: {}", e.what());
        return 1;
    }

    PG_LOG_INFO("Worker stopped gracefully.");
    return 0;
}

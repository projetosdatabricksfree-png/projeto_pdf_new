#include "printguard/common/logging.hpp"
#include "printguard/common/crypto.hpp"
#include "printguard/common/env.hpp"
#include "printguard/persistence/database.hpp"
#include "printguard/persistence/job_repository.hpp"
#include "printguard/storage/storage.hpp"
#include "printguard/domain/config_loader.hpp"
#include "printguard/orchestration/orchestrator.hpp"
#include <httplib.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
using namespace printguard;

int main() {
    common::Logger::init("printguard-api");
    PG_LOG_INFO("Starting PrintGuard API (Refactored)...");

    // 1. Initializations
    auto presets = domain::ConfigLoader::load_presets(common::Env::get("PRESETS_PATH", "./config/presets"));
    auto profiles = domain::ConfigLoader::load_profiles(common::Env::get("PROFILES_PATH", "./config/profiles"));

    try {
        persistence::Database::init(common::Env::get("PG_CONN_STR"));
    } catch (...) {
        PG_LOG_WARN("Database not reachable. Running in degraded mode.");
    }

    storage::LocalStorage store(common::Env::get("STORAGE_ROOT", "./storage_data"));
    orchestration::JobOrchestrator orchestrator(store);

    httplib::Server svr;

    // --- Endpoints ---

    svr.Get("/health", [](const httplib::Request&, httplib::Response& res) {
        json response = {{"status", "OK"}, {"service", "printguard-api"}, {"environment", common::Env::get("APP_ENV", "dev")}};
        res.set_content(response.dump(), "application/json");
    });

    svr.Get("/v1/presets", [&](const httplib::Request&, httplib::Response& res) {
        json response = json::array();
        for (auto const& [id, preset] : presets) {
            response.push_back(
                {{"id", preset.id},
                 {"name", preset.name},
                 {"dimensions", {preset.final_width_mm, preset.final_height_mm}}});
        }
        res.set_content(response.dump(), "application/json");
    });

    svr.Post("/v1/jobs", [&](const httplib::Request& req, httplib::Response& res) {
        if (!req.has_file("file")) {
            res.status = 400;
            res.set_content("{\"error\": \"Missing file\"}", "application/json");
            return;
        }

        std::string preset_id =
            req.has_param("preset_id") ? req.get_param_value("preset_id") : "business_card";
        std::string profile_id =
            req.has_param("profile_id") ? req.get_param_value("profile_id") : "printing_standard";

        if (presets.find(preset_id) == presets.end() || profiles.find(profile_id) == profiles.end()) {
            res.status = 400;
            res.set_content("{\"error\": \"Invalid preset_id or profile_id\"}", "application/json");
            return;
        }

        const auto& file = req.get_file_value("file");
        std::vector<char> data(file.content.begin(), file.content.end());

        // Process through Orchestrator
        auto result = orchestrator.process_upload(
            common::Env::get("DEFAULT_TENANT_ID", "00000000-0000-0000-0000-000000000000"),
            file.filename,
            data,
            preset_id,
            profile_id
        );

        if (result.success) {
            json response = {{"job_id", result.job_id}, {"status", domain::JobStatusValue::UPLOADED}};
            res.set_content(response.dump(), "application/json");
        } else {
            res.status = 500;
            json response = {{"error", result.error_message}};
            res.set_content(response.dump(), "application/json");
        }
    });

    int port = common::Env::get_int("PORT", 8080);
    PG_LOG_INFO("PrintGuard API listening on port {}", port);
    svr.listen("0.0.0.0", port);

    return 0;
}

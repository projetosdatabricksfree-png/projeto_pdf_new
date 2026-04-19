#include "printguard/persistence/database.hpp"
#include "printguard/common/logging.hpp"
#include "printguard/common/env.hpp"

namespace printguard::persistence {

std::string Database::s_conn_str;

void Database::init(const std::string& connection_string) {
    s_conn_str = connection_string.empty() ? common::Env::get("PG_CONN_STR") : connection_string;
    
    if (s_conn_str.empty()) {
        PG_LOG_ERROR("Database connection string is empty (PG_CONN_STR not set)");
        return;
    }
    
    // Initial verification
    try {
        pqxx::connection c(s_conn_str);
        PG_LOG_INFO("Successfully verified PostgreSQL connection string");
    } catch (const std::exception& e) {
        PG_LOG_ERROR("Failed to verify PostgreSQL connection: {}", e.what());
        throw;
    }
}

pqxx::connection& Database::get_connection() {
    static thread_local std::unique_ptr<pqxx::connection> t_conn;
    
    if (!t_conn || !t_conn->is_open()) {
        if (s_conn_str.empty()) {
            throw std::runtime_error("Database not initialized. Call Database::init() first.");
        }
        PG_LOG_DEBUG("Opening new thread-local database connection");
        t_conn = std::make_unique<pqxx::connection>(s_conn_str);
    }
    
    return *t_conn;
}

} // namespace printguard::persistence

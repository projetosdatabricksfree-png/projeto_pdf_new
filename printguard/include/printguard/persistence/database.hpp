#pragma once

#include <pqxx/pqxx>
#include <string>
#include <memory>
#include <mutex>

namespace printguard::persistence {

class Database {
public:
    static void init(const std::string& connection_string);
    static pqxx::connection& get_connection();

private:
    static std::string s_conn_str;
};

} // namespace printguard::persistence

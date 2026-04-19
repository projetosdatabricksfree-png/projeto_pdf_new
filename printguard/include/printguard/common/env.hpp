#pragma once
#include <string>
#include <cstdlib>

namespace printguard::common {

class Env {
public:
    static std::string get(const std::string& key, const std::string& default_val = "") {
        const char* val = std::getenv(key.c_str());
        return val ? std::string(val) : default_val;
    }
    
    static int get_int(const std::string& key, int default_val = 0) {
        const char* val = std::getenv(key.c_str());
        return val ? std::stoi(val) : default_val;
    }
};

} // namespace printguard::common

#pragma once
#include <string>
#include <vector>

namespace printguard::common {

class Crypto {
public:
    static std::string sha256(const std::vector<char>& data);
    static bool is_pdf(const std::vector<char>& data);
};

} // namespace printguard::common

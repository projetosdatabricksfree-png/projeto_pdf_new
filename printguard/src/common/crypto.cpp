#include "printguard/common/crypto.hpp"
#include <openssl/evp.h>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace printguard::common {

std::string Crypto::sha256(const std::vector<char>& data) {
    unsigned char hash[EVP_MAX_MD_SIZE];
    unsigned int hash_length = 0;

    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    if (ctx == nullptr) {
        throw std::runtime_error("Failed to allocate EVP_MD_CTX");
    }

    const int init_ok = EVP_DigestInit_ex(ctx, EVP_sha256(), nullptr);
    const int update_ok = EVP_DigestUpdate(ctx, data.data(), data.size());
    const int final_ok = EVP_DigestFinal_ex(ctx, hash, &hash_length);
    EVP_MD_CTX_free(ctx);

    if (init_ok != 1 || update_ok != 1 || final_ok != 1 || hash_length != 32U) {
        throw std::runtime_error("Failed to compute SHA256 digest");
    }

    std::stringstream ss;
    for (unsigned int i = 0; i < hash_length; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    }
    return ss.str();
}

bool Crypto::is_pdf(const std::vector<char>& data) {
    if (data.size() < 4) return false;
    // PDF Magic: %PDF-
    return (data[0] == '%' && data[1] == 'P' && data[2] == 'D' && data[3] == 'F');
}

} // namespace printguard::common

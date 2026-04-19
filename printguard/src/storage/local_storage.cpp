#include "printguard/storage/storage.hpp"
#include "printguard/common/logging.hpp"
#include <fstream>

namespace printguard::storage {

LocalStorage::LocalStorage(const std::string& root_path) : m_root(root_path) {
    if (!std::filesystem::exists(m_root)) {
        std::filesystem::create_directories(m_root);
    }
}

std::string LocalStorage::put(const std::string& job_id, const std::string& tenant_id, const std::string& type, const std::vector<char>& data) {
    // Structure: {root}/{tenant_id}/{job_id}/{type}/
    auto dir = m_root / tenant_id / job_id / type;
    std::filesystem::create_directories(dir);

    // For now, use fixed name or derived from filename? 
    // Skill says: "Original preserved". I'll use "original.pdf" for the type "original".
    std::string filename = (type == "original") ? "original.pdf" : (type + ".dat");
    auto full_path = dir / filename;

    std::ofstream ofs(full_path, std::ios::binary);
    if (!ofs) {
        throw std::runtime_error("Failed to open file for writing: " + full_path.string());
    }

    ofs.write(data.data(), data.size());
    ofs.close();

    PG_LOG_INFO("Saved artifact to {}", full_path.string());
    return full_path.string();
}

std::vector<char> LocalStorage::get(const std::string& path) {
    std::ifstream ifs(path, std::ios::binary | std::ios::ate);
    if (!ifs) {
        throw std::runtime_error("Failed to open file for reading: " + path);
    }

    auto size = ifs.tellg();
    std::vector<char> buffer(size);
    ifs.seekg(0, std::ios::beg);
    ifs.read(buffer.data(), size);

    return buffer;
}

void LocalStorage::remove(const std::string& path) {
    std::filesystem::remove(path);
}

} // namespace printguard::storage

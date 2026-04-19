#pragma once

#include <string>
#include <vector>
#include <filesystem>

namespace printguard::storage {

class IStorage {
public:
    virtual ~IStorage() = default;
    virtual std::string put(const std::string& job_id, const std::string& tenant_id, const std::string& type, const std::vector<char>& data) = 0;
    virtual std::vector<char> get(const std::string& path) = 0;
    virtual void remove(const std::string& path) = 0;
};

class LocalStorage : public IStorage {
public:
    LocalStorage(const std::string& root_path);
    std::string put(const std::string& job_id, const std::string& tenant_id, const std::string& type, const std::vector<char>& data) override;
    std::vector<char> get(const std::string& path) override;
    void remove(const std::string& path) override;

private:
    std::filesystem::path m_root;
};

} // namespace printguard::storage

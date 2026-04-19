#pragma once

#include <string>
#include <memory>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/basic_file_sink.h>

namespace printguard::common {

class Logger {
public:
    static void init(const std::string& app_name);
    static std::shared_ptr<spdlog::logger> get();

private:
    static std::shared_ptr<spdlog::logger> s_logger;
};

#define PG_LOG_INFO(...)  spdlog::info(__VA_ARGS__)
#define PG_LOG_WARN(...)  spdlog::warn(__VA_ARGS__)
#define PG_LOG_ERROR(...) spdlog::error(__VA_ARGS__)
#define PG_LOG_DEBUG(...) spdlog::debug(__VA_ARGS__)
#define PG_LOG_CRITICAL(...) spdlog::critical(__VA_ARGS__)

} // namespace printguard::common

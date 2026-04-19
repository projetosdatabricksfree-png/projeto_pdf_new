#include "printguard/common/logging.hpp"
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/basic_file_sink.h>
#include <vector>

namespace printguard::common {

std::shared_ptr<spdlog::logger> Logger::s_logger;

void Logger::init(const std::string& app_name) {
    auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
    console_sink->set_level(spdlog::level::info);
    
    // Pattern JSON-like for MVP
    console_sink->set_pattern("{\"timestamp\": \"%Y-%m-%dT%H:%M:%S.%f%z\", \"level\": \"%^%l%$\", \"service\": \""+ app_name +"\", \"msg\": \"%v\"}");

    std::vector<spdlog::sink_ptr> sinks { console_sink };
    
    s_logger = std::make_shared<spdlog::logger>(app_name, sinks.begin(), sinks.end());
    spdlog::set_default_logger(s_logger);
    spdlog::set_level(spdlog::level::debug);
}

std::shared_ptr<spdlog::logger> Logger::get() {
    return s_logger;
}

} // namespace printguard::common

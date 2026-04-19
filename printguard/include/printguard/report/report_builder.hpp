#pragma once

#include "printguard/orchestration/local_batch_processor.hpp"
#include <nlohmann/json.hpp>
#include <string>

namespace printguard::report {

class ReportBuilder {
public:
    static nlohmann::json build_technical_report(const orchestration::FileProcessResult& result);
    static nlohmann::json build_client_report(const orchestration::FileProcessResult& result);
    static std::string build_summary_markdown(const orchestration::FileProcessResult& result);
    static nlohmann::json build_batch_report(const orchestration::BatchProcessSummary& summary);
    static std::string build_batch_markdown(const orchestration::BatchProcessSummary& summary);
};

} // namespace printguard::report

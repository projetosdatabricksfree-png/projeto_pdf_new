#include "printguard/report/report_builder.hpp"

#include "printguard/domain/finding.hpp"
#include <algorithm>
#include <sstream>

namespace printguard::report {

namespace {

nlohmann::json finding_to_json(const domain::Finding& finding) {
    return {
        {"code", finding.code},
        {"rule_id", finding.rule_id},
        {"category", finding.category},
        {"severity", domain::to_string(finding.severity)},
        {"fixability", domain::to_string(finding.fixability)},
        {"page_number", finding.page_number},
        {"technical_message", finding.technical_message},
        {"user_message", finding.user_message},
        {"evidence", finding.evidence},
    };
}

nlohmann::json fix_to_json(const domain::FixRecord& record) {
    return {
        {"fix_id", record.fix_id},
        {"finding_code", record.finding_code},
        {"attempted", record.attempted},
        {"success", record.success},
        {"status", record.status},
        {"message", record.message},
        {"details", record.details},
    };
}

std::vector<std::string> successful_fix_messages(
    const std::vector<domain::FixRecord>& records) {
    std::vector<std::string> messages;
    for (auto const& record : records) {
        if (record.success) {
            messages.push_back(record.message);
        }
    }
    return messages;
}

std::vector<std::string> residual_messages(const orchestration::FileProcessResult& result) {
    std::vector<std::string> messages;
    for (auto const& finding : result.postfix_findings) {
        messages.push_back(finding.user_message);
    }
    for (auto const& error : result.errors) {
        messages.push_back(error);
    }
    return messages;
}

std::string findings_sentence(const std::vector<domain::Finding>& findings) {
    if (findings.empty()) {
        return "Nenhum problema relevante foi detectado.";
    }

    std::ostringstream out;
    for (std::size_t index = 0; index < findings.size(); ++index) {
        if (index > 0) {
            out << ' ';
        }
        out << findings[index].user_message;
    }
    return out.str();
}

std::string join_messages(const std::vector<std::string>& messages, std::string const& fallback) {
    if (messages.empty()) {
        return fallback;
    }

    std::ostringstream out;
    for (std::size_t index = 0; index < messages.size(); ++index) {
        if (index > 0) {
            out << ' ';
        }
        out << messages[index];
    }
    return out.str();
}

} // namespace

nlohmann::json ReportBuilder::build_technical_report(const orchestration::FileProcessResult& result) {
    nlohmann::json initial = nlohmann::json::array();
    for (auto const& finding : result.initial_findings) {
        initial.push_back(finding_to_json(finding));
    }

    nlohmann::json postfix = nlohmann::json::array();
    for (auto const& finding : result.postfix_findings) {
        postfix.push_back(finding_to_json(finding));
    }

    nlohmann::json fixes = nlohmann::json::array();
    for (auto const& fix : result.fixes_applied) {
        fixes.push_back(fix_to_json(fix));
    }

    return {
        {"report_version", "1.0"},
        {"original_filename", result.original_filename},
        {"original_path", result.original_path},
        {"checksum_sha256", result.checksum_sha256},
        {"preset_used", result.preset_id},
        {"validation_profile_used", result.profile_id},
        {"initial_findings", initial},
        {"fixes_applied", fixes},
        {"fixes_not_applied", result.fixes_not_applied},
        {"postfix_findings", postfix},
        {"revalidation", {{"resolved_codes", result.revalidation.resolved_codes},
                           {"remaining_codes", result.revalidation.remaining_codes},
                           {"introduced_codes", result.revalidation.introduced_codes}}},
        {"status_final", result.final_status},
        {"corrected_path", result.corrected_path},
        {"preview_path", result.preview_path},
        {"errors", result.errors},
        {"warnings", result.warnings},
        {"processing_time_ms",
         {{"analysis", result.analysis_ms},
          {"fix", result.fix_ms},
          {"revalidation", result.revalidation_ms},
          {"preview", result.preview_ms},
          {"report", result.report_ms},
          {"total", result.total_ms}}},
        {"correction_attempted", result.correction_attempted},
        {"correction_applied", result.correction_applied},
        {"corrected_is_passthrough", result.corrected_is_passthrough},
    };
}

nlohmann::json ReportBuilder::build_client_report(const orchestration::FileProcessResult& result) {
    auto fix_messages = successful_fix_messages(result.fixes_applied);
    auto residual = residual_messages(result);

    return {
        {"arquivo", result.original_filename},
        {"status_final", result.final_status},
        {"o_que_foi_detectado", findings_sentence(result.initial_findings)},
        {"o_que_foi_corrigido_automaticamente",
         join_messages(fix_messages, "Nenhuma correcao automatica segura foi aplicada.")},
        {"o_que_ainda_exige_atencao",
         join_messages(residual, "Nao restaram pendencias apos a revalidacao.")},
        {"fixes_aplicados", result.correction_applied},
        {"arquivo_saida", result.corrected_path},
    };
}

std::string ReportBuilder::build_summary_markdown(const orchestration::FileProcessResult& result) {
    std::ostringstream out;
    out << "# Resumo do arquivo\n\n";
    out << "- Arquivo original: `" << result.original_filename << "`\n";
    out << "- Status final: `" << result.final_status << "`\n";
    out << "- Preset usado: `" << result.preset_id << "`\n";
    out << "- Perfil usado: `" << result.profile_id << "`\n";
    out << "- Findings iniciais: `" << result.initial_findings.size() << "`\n";
    out << "- Findings apos correcao: `" << result.postfix_findings.size() << "`\n";
    out << "- Correcao aplicada: `" << (result.correction_applied ? "sim" : "nao") << "`\n";
    out << "- Saida gerada: `" << result.corrected_path << "`\n";
    if (!result.errors.empty()) {
        out << "- Erros: `" << result.errors.size() << "`\n";
    }
    if (!result.warnings.empty()) {
        out << "- Warnings: `" << result.warnings.size() << "`\n";
    }
    return out.str();
}

nlohmann::json ReportBuilder::build_batch_report(const orchestration::BatchProcessSummary& summary) {
    nlohmann::json files = nlohmann::json::array();
    for (auto const& file : summary.files) {
        files.push_back({
            {"arquivo", file.original_filename},
            {"status_final", file.final_status},
            {"corrected_path", file.corrected_path},
            {"technical_report_path", file.technical_report_path},
            {"client_report_path", file.client_report_path},
            {"summary_path", file.summary_path},
        });
    }

    return {
        {"total_files", summary.total_files},
        {"completed_files", summary.completed_files},
        {"manual_review_files", summary.manual_review_files},
        {"failed_files", summary.failed_files},
        {"files", files},
    };
}

std::string ReportBuilder::build_batch_markdown(const orchestration::BatchProcessSummary& summary) {
    std::ostringstream out;
    out << "# Relatorio do lote\n\n";
    out << "- Total de arquivos: `" << summary.total_files << "`\n";
    out << "- Concluidos: `" << summary.completed_files << "`\n";
    out << "- Revisao manual: `" << summary.manual_review_files << "`\n";
    out << "- Falhas: `" << summary.failed_files << "`\n\n";

    out << "| Arquivo | Status | Relatorio tecnico |\n";
    out << "| --- | --- | --- |\n";
    for (auto const& file : summary.files) {
        out << "| " << file.original_filename << " | " << file.final_status << " | "
            << file.technical_report_path << " |\n";
    }

    return out.str();
}

} // namespace printguard::report

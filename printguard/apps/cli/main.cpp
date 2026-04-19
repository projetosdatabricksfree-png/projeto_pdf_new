#include "printguard/common/logging.hpp"
#include "printguard/common/version.hpp"
#include "printguard/domain/config_loader.hpp"
#include "printguard/orchestration/local_batch_processor.hpp"
#include <exception>
#include <iostream>

using namespace printguard;

int main(int argc, char** argv) {
    common::Logger::init("printguard-cli");

    const std::string input_dir =
        argc > 1 ? argv[1] : "/home/diego/Documents/ARQUIVOS_TESTE";
    const std::string corrected_dir =
        argc > 2 ? argv[2] : "/home/diego/Documents/Corrigidos";
    const std::string report_dir =
        argc > 3 ? argv[3] : "/home/diego/Documents/RELATORIO";
    const std::string preset_id = argc > 4 ? argv[4] : "auto";
    const std::string profile_id = argc > 5 ? argv[5] : "printing_standard";

    try {
        auto presets = domain::ConfigLoader::load_presets("./config/presets");
        auto profiles = domain::ConfigLoader::load_profiles("./config/profiles");
        orchestration::LocalBatchProcessor processor(std::move(presets), std::move(profiles));
        auto summary = processor.process_directory(
            input_dir, corrected_dir, report_dir, preset_id, profile_id);

        std::cout << "PrintGuard " << common::kPrintGuardVersion << '\n';
        std::cout << "Arquivos processados: " << summary.total_files << '\n';
        std::cout << "Concluidos: " << summary.completed_files << '\n';
        std::cout << "Revisao manual: " << summary.manual_review_files << '\n';
        std::cout << "Falhas: " << summary.failed_files << '\n';
        std::cout << "Relatorio do lote: " << summary.batch_report_markdown_path << '\n';
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Erro no lote: " << e.what() << '\n';
        return 1;
    }
}

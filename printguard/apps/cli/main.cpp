#include "printguard/common/logging.hpp"
#include "printguard/common/version.hpp"
#include "printguard/domain/config_loader.hpp"
#include "printguard/orchestration/local_batch_processor.hpp"
#include <exception>
#include <iostream>

using namespace printguard;

int main(int argc, char** argv) {
    common::Logger::init("printguard-cli");

    std::string input_dir = "/home/diego/Documents/ARQUIVOS_TESTE";
    std::string corrected_dir = "/home/diego/Documents/Corrigidos";
    std::string report_dir = "/home/diego/Documents/RELATORIO";
    std::string preset_id = "auto";
    std::string profile_id = "printing_standard";

    int positional_index = 0;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--preset" && (i + 1) < argc) {
            preset_id = argv[++i];
            continue;
        }
        if (arg == "--profile" && (i + 1) < argc) {
            profile_id = argv[++i];
            continue;
        }

        switch (positional_index) {
            case 0:
                input_dir = arg;
                break;
            case 1:
                corrected_dir = arg;
                break;
            case 2:
                report_dir = arg;
                break;
            case 3:
                preset_id = arg;
                break;
            case 4:
                profile_id = arg;
                break;
            default:
                break;
        }
        ++positional_index;
    }

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

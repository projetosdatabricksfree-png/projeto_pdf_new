#include "printguard/pdf/pdf_loader.hpp"
#include "printguard/common/logging.hpp"
#include <iostream>
#include <iomanip>

using namespace printguard;

void print_box(const std::string& name, const pdf::Rect& r) {
    std::cout << "  " << std::left << std::setw(10) << name << ": "
              << std::fixed << std::setprecision(2)
              << r.w << " x " << r.h << " mm (pos: " << r.x << ", " << r.y << ")" << std::endl;
}

int main(int argc, char** argv) {
    common::Logger::init("printguard-inspect");

    if (argc < 2) {
        std::cerr << "Usage: printguard-inspect <pdf_file>" << std::endl;
        return 1;
    }

    try {
        std::string path = argv[1];
        auto model = pdf::PdfLoader::load_from_file(path);

        std::cout << "--- PrintGuard PDF Inspection ---" << std::endl;
        std::cout << "File: " << path << std::endl;
        std::cout << "Pages: " << model.page_count << std::endl;
        std::cout << "Version: " << model.metadata.pdf_version << std::endl;
        std::cout << "Producer: " << model.metadata.producer << std::endl;
        std::cout << "Linearized: " << (model.metadata.is_linearized ? "Yes" : "No") << std::endl;
        std::cout << "Encrypted: " << (model.metadata.is_encrypted ? "Yes" : "No") << std::endl;
        std::cout << std::endl;

        for (const auto& page : model.pages) {
            std::cout << "Page " << page.number << ":" << std::endl;
            std::cout << "  Rotation: " << page.rotation << " deg" << std::endl;
            print_box("MediaBox", page.media_box);
            print_box("TrimBox", page.trim_box);
            print_box("BleedBox", page.bleed_box);
            print_box("CropBox", page.crop_box);
            std::cout << std::endl;
        }

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}

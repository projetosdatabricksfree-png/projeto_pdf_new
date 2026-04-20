#include <catch2/catch_test_macros.hpp>

#include "printguard/domain/config_loader.hpp"
#include "printguard/orchestration/local_batch_processor.hpp"

#include <algorithm>
#include <fstream>
#include <filesystem>
#include <nlohmann/json.hpp>
#include <qpdf/QPDF.hh>
#include <qpdf/QPDFObjectHandle.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <qpdf/QPDFWriter.hh>
#include <string>
#include <vector>

using namespace printguard;

namespace {

std::filesystem::path project_root() {
    return PRINTGUARD_TEST_PROJECT_SOURCE_DIR;
}

std::string shell_escape(std::string const& input) {
    std::string escaped = "'";
    for (char ch : input) {
        if (ch == '\'') {
            escaped += "'\\''";
        } else {
            escaped += ch;
        }
    }
    escaped += "'";
    return escaped;
}

double mm_to_pt(double mm) {
    return mm * 72.0 / 25.4;
}

std::filesystem::path make_temp_dir(std::string const& stem) {
    static int counter = 0;
    ++counter;
    auto dir = std::filesystem::temp_directory_path() /
        (stem + "_" + std::to_string(counter));
    std::filesystem::create_directories(dir);
    return dir;
}

QPDFObjectHandle make_box_pts(double left, double bottom, double right, double top) {
    return QPDFObjectHandle::newArray(
        {QPDFObjectHandle::newReal(left),
         QPDFObjectHandle::newReal(bottom),
         QPDFObjectHandle::newReal(right),
         QPDFObjectHandle::newReal(top)});
}

QPDFObjectHandle make_image(
    QPDF& pdf,
    int width,
    int height,
    QPDFObjectHandle const& color_space,
    std::vector<unsigned char> const& raw,
    int bits_per_component = 8) {
    std::string bytes(reinterpret_cast<char const*>(raw.data()), raw.size());
    QPDFObjectHandle image = pdf.newStream(bytes);
    auto dict = image.getDict();
    dict.replaceKey("/Type", QPDFObjectHandle::newName("/XObject"));
    dict.replaceKey("/Subtype", QPDFObjectHandle::newName("/Image"));
    dict.replaceKey("/Width", QPDFObjectHandle::newInteger(width));
    dict.replaceKey("/Height", QPDFObjectHandle::newInteger(height));
    dict.replaceKey("/ColorSpace", color_space);
    dict.replaceKey("/BitsPerComponent", QPDFObjectHandle::newInteger(bits_per_component));
    return pdf.makeIndirectObject(image);
}

std::filesystem::path write_pdf(QPDF& pdf, std::filesystem::path const& path) {
    QPDFWriter writer(pdf, path.string().c_str());
    writer.setStaticID(true);
    writer.setCompressStreams(false);
    writer.write();
    return path;
}

std::vector<char> read_file_bytes(std::filesystem::path const& path) {
    std::ifstream ifs(path, std::ios::binary | std::ios::ate);
    REQUIRE(ifs.good());
    auto size = ifs.tellg();
    std::vector<char> buffer(static_cast<std::size_t>(size));
    ifs.seekg(0);
    ifs.read(buffer.data(), size);
    return buffer;
}

nlohmann::json read_json(std::filesystem::path const& path) {
    std::ifstream ifs(path);
    REQUIRE(ifs.good());
    return nlohmann::json::parse(ifs);
}

bool has_string(std::vector<std::string> const& values, std::string const& expected) {
    return std::find(values.begin(), values.end(), expected) != values.end();
}

bool command_exists(std::string const& name) {
    std::string command = "command -v " + name + " >/dev/null 2>&1";
    return std::system(command.c_str()) == 0;
}

std::filesystem::path build_business_card_rgb_pdf(std::filesystem::path const& path) {
    QPDF pdf;
    pdf.emptyPDF();

    double media_w = mm_to_pt(96.0);
    double media_h = mm_to_pt(56.0);
    double trim_offset = mm_to_pt(3.0);
    double trim_w = mm_to_pt(90.0);
    double trim_h = mm_to_pt(50.0);

    QPDFObjectHandle resources = QPDFObjectHandle::newDictionary();
    std::string content =
        "q\n"
        "0.9 0.2 0.1 rg\n"
        "20 20 120 60 re f\n"
        "Q\n";
    QPDFObjectHandle contents = pdf.makeIndirectObject(pdf.newStream(content));

    QPDFObjectHandle page = QPDFObjectHandle::newDictionary();
    page.replaceKey("/Type", QPDFObjectHandle::newName("/Page"));
    page.replaceKey("/MediaBox", make_box_pts(0, 0, media_w, media_h));
    page.replaceKey("/BleedBox", make_box_pts(0, 0, media_w, media_h));
    page.replaceKey(
        "/TrimBox",
        make_box_pts(trim_offset, trim_offset, trim_offset + trim_w, trim_offset + trim_h));
    page.replaceKey("/Resources", resources);
    page.replaceKey("/Contents", contents);

    QPDFPageDocumentHelper helper(pdf);
    helper.addPage(QPDFPageObjectHelper(page), false);
    return write_pdf(pdf, path);
}

std::filesystem::path build_tcc_pdf(std::filesystem::path const& path) {
    QPDF pdf;
    pdf.emptyPDF();

    double media_w = mm_to_pt(210.0);
    double media_h = mm_to_pt(297.0);

    QPDFObjectHandle resources = QPDFObjectHandle::newDictionary();
    std::string content =
        "q\n"
        "0 g\n"
        "36 36 200 60 re f\n"
        "Q\n";
    QPDFObjectHandle contents = pdf.makeIndirectObject(pdf.newStream(content));

    QPDFObjectHandle page = QPDFObjectHandle::newDictionary();
    page.replaceKey("/Type", QPDFObjectHandle::newName("/Page"));
    page.replaceKey("/MediaBox", make_box_pts(0, 0, media_w, media_h));
    page.replaceKey("/TrimBox", make_box_pts(0, 0, media_w, media_h));
    page.replaceKey("/Resources", resources);
    page.replaceKey("/Contents", contents);

    QPDFPageDocumentHelper helper(pdf);
    helper.addPage(QPDFPageObjectHelper(page), false);
    return write_pdf(pdf, path);
}

std::filesystem::path build_low_res_business_card_pdf(std::filesystem::path const& path) {
    QPDF pdf;
    pdf.emptyPDF();

    double media_w = mm_to_pt(96.0);
    double media_h = mm_to_pt(56.0);
    double trim_offset = mm_to_pt(3.0);
    double trim_w = mm_to_pt(90.0);
    double trim_h = mm_to_pt(50.0);

    std::vector<unsigned char> gray_pixels(10 * 10, 0x90);
    QPDFObjectHandle resources = QPDFObjectHandle::newDictionary();
    QPDFObjectHandle xobject = QPDFObjectHandle::newDictionary();
    xobject.replaceKey(
        "/Im1",
        make_image(
            pdf,
            10,
            10,
            QPDFObjectHandle::newName("/DeviceGray"),
            gray_pixels));
    resources.replaceKey("/XObject", xobject);

    std::string content =
        "q\n"
        + std::to_string(trim_w) + " 0 0 " + std::to_string(trim_h) + " "
        + std::to_string(trim_offset) + " " + std::to_string(trim_offset) + " cm\n"
        + "/Im1 Do\n"
        + "Q\n";
    QPDFObjectHandle contents = pdf.makeIndirectObject(pdf.newStream(content));

    QPDFObjectHandle page = QPDFObjectHandle::newDictionary();
    page.replaceKey("/Type", QPDFObjectHandle::newName("/Page"));
    page.replaceKey("/MediaBox", make_box_pts(0, 0, media_w, media_h));
    page.replaceKey(
        "/TrimBox",
        make_box_pts(trim_offset, trim_offset, trim_offset + trim_w, trim_offset + trim_h));
    page.replaceKey("/Resources", resources);
    page.replaceKey("/Contents", contents);

    QPDFPageDocumentHelper helper(pdf);
    helper.addPage(QPDFPageObjectHelper(page), false);
    return write_pdf(pdf, path);
}

std::map<std::string, domain::ProductPreset> load_presets() {
    return domain::ConfigLoader::load_presets((project_root() / "config" / "presets").string());
}

std::map<std::string, domain::ValidationProfile> load_profiles() {
    return domain::ConfigLoader::load_profiles((project_root() / "config" / "profiles").string());
}

} // namespace

TEST_CASE("CLI processes RGB business card pipeline end-to-end", "[fix][h11]") {
    auto workspace = make_temp_dir("printguard_h11_cli_rgb");
    auto input_dir = workspace / "input";
    auto corrected_dir = workspace / "corrected";
    auto report_dir = workspace / "reports";
    std::filesystem::create_directories(input_dir);
    std::filesystem::create_directories(corrected_dir);
    std::filesystem::create_directories(report_dir);

    auto input_pdf = build_business_card_rgb_pdf(input_dir / "rgb_business_card.pdf");
    auto original_bytes = read_file_bytes(input_pdf);

    std::string command =
        "cd " + shell_escape(project_root().string()) + " && " +
        shell_escape(PRINTGUARD_TEST_CLI_PATH) + " " +
        shell_escape(input_dir.string()) + " " +
        shell_escape(corrected_dir.string()) + " " +
        shell_escape(report_dir.string()) + " --preset business_card_90x50 --profile digital_print_standard";
    REQUIRE(std::system(command.c_str()) == 0);

    auto technical_report = report_dir / "rgb_business_card_relatorio_tecnico.json";
    auto client_report = report_dir / "rgb_business_card_relatorio_cliente.json";
    auto summary_report = report_dir / "rgb_business_card_resumo.md";
    REQUIRE(std::filesystem::exists(technical_report));
    REQUIRE(std::filesystem::exists(client_report));
    REQUIRE(std::filesystem::exists(summary_report));

    auto technical = read_json(technical_report);
    auto client = read_json(client_report);

    REQUIRE(technical.at("preset_used") == "business_card_90x50");
    REQUIRE(technical.at("preset_family") == "quick_print");
    REQUIRE(technical.at("validation_profile_used") == "digital_print_standard");
    REQUIRE(client.at("status_final") == "completed");
    REQUIRE(technical.at("corrected_path").get<std::string>() != input_pdf.string());

    std::vector<std::string> initial_codes;
    for (auto const& finding : technical.at("initial_findings")) {
        initial_codes.push_back(finding.at("code").get<std::string>());
    }
    std::vector<std::string> resolved_codes =
        technical.at("revalidation").at("resolved_codes").get<std::vector<std::string>>();
    REQUIRE(has_string(initial_codes, "PG_ERR_RGB_COLORSPACE"));
    REQUIRE(has_string(resolved_codes, "PG_ERR_RGB_COLORSPACE"));

    if (command_exists("mutool")) {
        REQUIRE(technical.at("preview_generated").get<bool>());
        REQUIRE(std::filesystem::exists(technical.at("preview_path").get<std::string>()));
    } else {
        REQUIRE_FALSE(technical.at("preview_generated").get<bool>());
        REQUIRE_FALSE(technical.at("warnings").get<std::vector<std::string>>().empty());
    }

    REQUIRE(read_file_bytes(input_pdf) == original_bytes);
}

TEST_CASE("CLI accepts document preset and profile aliases", "[fix][h11]") {
    auto workspace = make_temp_dir("printguard_h11_cli_docs");
    auto input_dir = workspace / "input";
    auto corrected_dir = workspace / "corrected";
    auto report_dir = workspace / "reports";
    std::filesystem::create_directories(input_dir);
    std::filesystem::create_directories(corrected_dir);
    std::filesystem::create_directories(report_dir);

    auto input_pdf = build_tcc_pdf(input_dir / "tcc_document.pdf");
    REQUIRE(std::filesystem::exists(input_pdf));

    std::string command =
        "cd " + shell_escape(project_root().string()) + " && " +
        shell_escape(PRINTGUARD_TEST_CLI_PATH) + " " +
        shell_escape(input_dir.string()) + " " +
        shell_escape(corrected_dir.string()) + " " +
        shell_escape(report_dir.string()) + " --preset tcc_a4 --profile books_and_documents";
    REQUIRE(std::system(command.c_str()) == 0);

    auto technical = read_json(report_dir / "tcc_document_relatorio_tecnico.json");
    REQUIRE(technical.at("preset_used") == "tcc_a4");
    REQUIRE(technical.at("preset_family") == "documents_and_books");
    REQUIRE(technical.at("validation_profile_used") == "books_and_documents");
    REQUIRE(technical.at("status_final") == "completed");
}

TEST_CASE("LocalBatchProcessor marks manual review when blocking finding remains", "[fix][h11]") {
    auto presets = load_presets();
    auto profiles = load_profiles();
    orchestration::LocalBatchProcessor processor(presets, profiles);

    auto workspace = make_temp_dir("printguard_h11_manual_review");
    auto input_pdf = build_low_res_business_card_pdf(workspace / "low_res.pdf");
    auto result = processor.process_file(
        input_pdf.string(),
        (workspace / "corrected").string(),
        (workspace / "reports").string(),
        presets.at("business_card_90x50"),
        profiles.at("digital_print_standard"));

    REQUIRE(result.final_status == "manual_review_required");
    REQUIRE(result.has_blocking_unresolved);
    REQUIRE(result.needs_manual_review);
    REQUIRE_FALSE(result.manual_review_reasons.empty());
    REQUIRE(has_string(result.fixes_not_applied, "PG_ERR_LOW_RES"));
}

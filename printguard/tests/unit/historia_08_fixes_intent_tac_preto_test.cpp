#include <catch2/catch_test_macros.hpp>

#include "printguard/domain/finding.hpp"
#include "printguard/domain/preset.hpp"
#include "printguard/fix/fix_engine.hpp"
#include "printguard/fix/fix_interface.hpp"
#include "printguard/fix/fixes/attach_output_intent_fix.hpp"
#include "printguard/fix/fixes/black_normalization_fix.hpp"
#include "printguard/fix/fixes/tac_reduction_fix.hpp"

#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <functional>
#include <qpdf/QPDF.hh>
#include <qpdf/QPDFObjectHandle.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <qpdf/QPDFWriter.hh>
#include <string>
#include <vector>

using namespace printguard;

namespace {

std::filesystem::path write_temp_pdf(QPDF& pdf, const std::string& filename) {
    auto path = std::filesystem::temp_directory_path() / filename;
    QPDFWriter writer(pdf, path.string().c_str());
    writer.setStaticID(true);
    writer.setCompressStreams(false);
    writer.write();
    return path;
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
    const QPDFObjectHandle& color_space,
    const std::vector<unsigned char>& raw,
    int bits_per_component = 8) {
    std::string bytes(reinterpret_cast<const char*>(raw.data()), raw.size());
    QPDFObjectHandle image = pdf.newStream(bytes);
    QPDFObjectHandle dict = image.getDict();
    dict.replaceKey("/Type", QPDFObjectHandle::newName("/XObject"));
    dict.replaceKey("/Subtype", QPDFObjectHandle::newName("/Image"));
    dict.replaceKey("/Width", QPDFObjectHandle::newInteger(width));
    dict.replaceKey("/Height", QPDFObjectHandle::newInteger(height));
    dict.replaceKey("/ColorSpace", color_space);
    dict.replaceKey("/BitsPerComponent", QPDFObjectHandle::newInteger(bits_per_component));
    return pdf.makeIndirectObject(image);
}

std::filesystem::path build_pdf_with_single_page(
    const std::string& content_stream,
    std::function<void(QPDF&, QPDFObjectHandle& resources)> configure_resources) {
    QPDF pdf;
    pdf.emptyPDF();

    QPDFObjectHandle resources = QPDFObjectHandle::newDictionary();
    configure_resources(pdf, resources);

    QPDFObjectHandle contents = pdf.makeIndirectObject(pdf.newStream(content_stream));

    QPDFObjectHandle page = QPDFObjectHandle::newDictionary();
    page.replaceKey("/Type", QPDFObjectHandle::newName("/Page"));
    page.replaceKey("/MediaBox", make_box_pts(0, 0, 200, 200));
    page.replaceKey("/TrimBox", make_box_pts(0, 0, 200, 200));
    page.replaceKey("/Resources", resources);
    page.replaceKey("/Contents", contents);

    QPDFPageDocumentHelper pdh(pdf);
    pdh.addPage(QPDFPageObjectHelper(page), false);

    static int counter = 0;
    ++counter;
    return write_temp_pdf(pdf, "printguard_h08_" + std::to_string(counter) + ".pdf");
}

std::vector<unsigned char> read_stream_bytes(QPDFObjectHandle stream) {
    auto data = stream.getStreamData(qpdf_dl_generalized);
    auto const* begin = reinterpret_cast<const unsigned char*>(data->getBuffer());
    return std::vector<unsigned char>(begin, begin + data->getSize());
}

std::string read_stream(QPDFObjectHandle stream) {
    auto data = stream.getStreamData(qpdf_dl_generalized);
    return {reinterpret_cast<const char*>(data->getBuffer()), data->getSize()};
}

std::string read_page_content(QPDFPageObjectHelper& page) {
    std::string content;
    for (auto& stream : page.getPageContents()) {
        content += read_stream(stream);
    }
    return content;
}

domain::ProductPreset preset_with_profile() {
    domain::ProductPreset preset;
    preset.color_policy.output_intent_profile = "GRACoL2013.icc";
    preset.max_total_ink_percent = 320;
    return preset;
}

std::filesystem::path temp_output_path(const std::string& stem) {
    static int counter = 0;
    ++counter;
    return std::filesystem::temp_directory_path() /
        (stem + "_" + std::to_string(counter) + ".pdf");
}

void require_qpdf_check(const std::filesystem::path& path) {
    std::string command = "qpdf --check \"" + path.string() + "\" > /dev/null 2>&1";
    REQUIRE(std::system(command.c_str()) == 0);
}

domain::Finding output_intent_finding() {
    return {
        "PG_ERR_MISSING_OUTPUT_INTENT",
        "OutputIntentRule",
        "color",
        domain::FindingSeverity::ERROR,
        domain::Fixability::AUTOMATIC_SAFE,
        0,
        "Missing output intent",
        "Missing output intent",
        {}};
}

domain::Finding tac_finding() {
    return {
        "PG_ERR_TAC_EXCEEDED",
        "TacRule",
        "color",
        domain::FindingSeverity::ERROR,
        domain::Fixability::AUTOMATIC_SAFE,
        1,
        "TAC too high",
        "TAC too high",
        {}};
}

domain::Finding rich_black_finding() {
    return {
        "PG_WARN_RICH_BLACK_TEXT",
        "BlackConsistencyRule",
        "color",
        domain::FindingSeverity::WARNING,
        domain::Fixability::AUTOMATIC_SAFE,
        1,
        "Rich black text",
        "Rich black text",
        {}};
}

} // namespace

TEST_CASE("AttachOutputIntentFix attaches ICC profile and validates output PDF", "[fix][h08]") {
    auto input = build_pdf_with_single_page("q\nQ\n", [](QPDF&, QPDFObjectHandle&) {});
    auto output = temp_output_path("printguard_h08_output_intent");

    auto engine = fix::create_default_fix_engine();
    fix::FixPlanner planner;
    std::vector<domain::Finding> findings = {output_intent_finding()};
    auto plan = planner.build_plan(findings, *engine, preset_with_profile());
    auto result =
        engine->execute(input.string(), output.string(), plan, findings, preset_with_profile());

    REQUIRE(result.changes_applied);
    REQUIRE(std::any_of(
        result.records.begin(),
        result.records.end(),
        [](const domain::FixRecord& record) { return record.fix_id == "AttachOutputIntentFix"; }));
    require_qpdf_check(output);

    QPDF pdf;
    pdf.processFile(output.string().c_str());
    QPDFObjectHandle output_intents = pdf.getRoot().getKey("/OutputIntents");
    REQUIRE(output_intents.isArray());
    REQUIRE(output_intents.getArrayNItems() == 1);

    QPDFObjectHandle output_intent = output_intents.getArrayItem(0);
    REQUIRE(output_intent.getKey("/Type").getName() == "/OutputIntent");
    REQUIRE(output_intent.getKey("/S").getName() == "/GTS_PDFX");
    REQUIRE(output_intent.getKey("/OutputConditionIdentifier").getUTF8Value() == "GRACoL2013.icc");

    QPDFObjectHandle profile_stream = output_intent.getKey("/DestOutputProfile");
    REQUIRE(profile_stream.isStream());
    REQUIRE(profile_stream.getDict().getKey("/N").getIntValueAsInt() == 4);
}

TEST_CASE("TacReductionFix reduces CMYK image TAC to the preset ceiling", "[fix][h08]") {
    std::vector<unsigned char> cmyk_bytes = {255, 255, 255, 255};
    auto input = build_pdf_with_single_page(
        "q\n/Im1 Do\nQ\n",
        [&](QPDF& pdf, QPDFObjectHandle& resources) {
            QPDFObjectHandle xobject = QPDFObjectHandle::newDictionary();
            xobject.replaceKey(
                "/Im1",
                make_image(
                    pdf,
                    1,
                    1,
                    QPDFObjectHandle::newName("/DeviceCMYK"),
                    cmyk_bytes));
            resources.replaceKey("/XObject", xobject);
        });

    auto output = temp_output_path("printguard_h08_tac");
    auto engine = fix::create_default_fix_engine();
    fix::FixPlanner planner;
    std::vector<domain::Finding> findings = {tac_finding()};
    auto plan = planner.build_plan(findings, *engine, preset_with_profile());
    auto result =
        engine->execute(input.string(), output.string(), plan, findings, preset_with_profile());

    REQUIRE(result.changes_applied);
    REQUIRE(std::any_of(
        result.records.begin(),
        result.records.end(),
        [](const domain::FixRecord& record) { return record.fix_id == "TacReductionFix"; }));
    require_qpdf_check(output);

    QPDF pdf;
    pdf.processFile(output.string().c_str());
    auto image = QPDFPageDocumentHelper(pdf).getAllPages().front().getImages().at("/Im1");
    auto adjusted = read_stream_bytes(image);
    REQUIRE(adjusted.size() == 4);

    double total_percent = (static_cast<double>(adjusted[0]) + adjusted[1] + adjusted[2] +
                               adjusted[3]) /
        255.0 * 100.0;
    REQUIRE(total_percent <= 320.5);
    REQUIRE(adjusted[3] == 255);
}

TEST_CASE("BlackNormalizationFix only normalizes rich black inside text blocks", "[fix][h08]") {
    auto input = build_pdf_with_single_page(
        "q\n0.2 0.1 0.1 1 k\n0 0 20 20 re f\nBT\n/F1 12 Tf\n0.2 0.1 0.1 1 k\n10 10 Td\n(Hello) Tj\nET\nQ\n",
        [](QPDF&, QPDFObjectHandle& resources) {
            resources.replaceKey("/Font", QPDFObjectHandle::newDictionary());
        });

    auto output = temp_output_path("printguard_h08_black");
    auto engine = fix::create_default_fix_engine();
    fix::FixPlanner planner;
    std::vector<domain::Finding> findings = {rich_black_finding()};
    auto plan = planner.build_plan(findings, *engine, preset_with_profile());
    auto result =
        engine->execute(input.string(), output.string(), plan, findings, preset_with_profile());

    REQUIRE(result.changes_applied);
    REQUIRE(std::any_of(
        result.records.begin(),
        result.records.end(),
        [](const domain::FixRecord& record) {
            return record.fix_id == "BlackNormalizationFix";
        }));
    require_qpdf_check(output);

    QPDF pdf;
    pdf.processFile(output.string().c_str());
    auto page = QPDFPageDocumentHelper(pdf).getAllPages().front();
    std::string content = read_page_content(page);
    REQUIRE(content.find("0.2 0.1 0.1 1 k\n0 0 20 20 re f") != std::string::npos);
    REQUIRE(content.find("BT\n/F1 12 Tf\n0 0 0 1 k\n10 10 Td") != std::string::npos);
}

#include <catch2/catch_test_macros.hpp>

#include "printguard/domain/finding.hpp"
#include "printguard/domain/preset.hpp"
#include "printguard/fix/fix_engine.hpp"
#include "printguard/fix/fix_interface.hpp"
#include "printguard/fix/fixes/image_color_convert_fix.hpp"

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <functional>
#include <qpdf/Buffer.hh>
#include <qpdf/QPDF.hh>
#include <qpdf/QPDFObjectHandle.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <qpdf/QPDFWriter.hh>
#include <string>
#include <vector>

using namespace printguard;

namespace {

std::filesystem::path write_temp_pdf(QPDF& pdf, std::string const& filename) {
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
    QPDFObjectHandle const& color_space,
    std::vector<unsigned char> const& raw,
    int bits_per_component = 8) {
    std::string bytes(reinterpret_cast<char const*>(raw.data()), raw.size());
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
    std::string const& content_stream,
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
    return write_temp_pdf(pdf, "printguard_h07_" + std::to_string(counter) + ".pdf");
}

std::string read_stream(QPDFObjectHandle stream) {
    auto data = stream.getStreamData(qpdf_dl_generalized);
    return {reinterpret_cast<char const*>(data->getBuffer()), data->getSize()};
}

std::vector<unsigned char> read_stream_bytes(QPDFObjectHandle stream) {
    auto data = stream.getStreamData(qpdf_dl_generalized);
    auto const* begin = reinterpret_cast<unsigned char const*>(data->getBuffer());
    return std::vector<unsigned char>(begin, begin + data->getSize());
}

std::string read_page_content(QPDFPageObjectHelper& page) {
    std::string content;
    for (auto& stream : page.getPageContents()) {
        content += read_stream(stream);
    }
    return content;
}

domain::Finding rgb_finding() {
    return {
        "PG_ERR_RGB_COLORSPACE",
        "ColorSpaceRule",
        "color",
        domain::FindingSeverity::ERROR,
        domain::Fixability::AUTOMATIC_SAFE,
        1,
        "RGB found",
        "RGB found",
        {}};
}

domain::ProductPreset preset_with_profile() {
    domain::ProductPreset preset;
    preset.color_policy.output_intent_profile = "GRACoL2013.icc";
    return preset;
}

std::filesystem::path temp_output_path(std::string const& stem) {
    static int counter = 0;
    ++counter;
    return std::filesystem::temp_directory_path() /
        (stem + "_" + std::to_string(counter) + ".pdf");
}

void require_qpdf_check(std::filesystem::path const& path) {
    std::string command = "qpdf --check \"" + path.string() + "\" > /dev/null 2>&1";
    REQUIRE(std::system(command.c_str()) == 0);
}

} // namespace

TEST_CASE("Default fix engine converts RGB operators and RGB images with lcms2", "[fix][h07]") {
    auto input = build_pdf_with_single_page(
        "q\n0.9 0.2 0.1 rg\n0.5 0.5 0.5 RG\n10 10 50 50 re f\n/Im1 Do\nQ\n",
        [&](QPDF& pdf, QPDFObjectHandle& resources) {
            std::vector<unsigned char> rgb_bytes = {255, 0, 0};
            QPDFObjectHandle xobject = QPDFObjectHandle::newDictionary();
            xobject.replaceKey(
                "/Im1",
                make_image(
                    pdf,
                    1,
                    1,
                    QPDFObjectHandle::newName("/DeviceRGB"),
                    rgb_bytes));
            resources.replaceKey("/XObject", xobject);
        });

    auto output = temp_output_path("printguard_h07_engine");

    auto engine = fix::create_default_fix_engine();
    fix::FixPlanner planner;
    std::vector<domain::Finding> findings = {rgb_finding()};
    auto plan = planner.build_plan(findings, *engine, preset_with_profile());
    auto result =
        engine->execute(input.string(), output.string(), plan, findings, preset_with_profile());

    REQUIRE(result.output_generated);
    REQUIRE(result.changes_applied);
    REQUIRE(
        std::any_of(
            result.records.begin(),
            result.records.end(),
            [](domain::FixRecord const& record) { return record.fix_id == "ConvertRgbToCmykFix"; }));
    REQUIRE(
        std::any_of(
            result.records.begin(),
            result.records.end(),
            [](domain::FixRecord const& record) { return record.fix_id == "ImageColorConvertFix"; }));

    require_qpdf_check(output);

    QPDF pdf;
    pdf.processFile(output.string().c_str());
    QPDFPageDocumentHelper helper(pdf);
    auto pages = helper.getAllPages();
    REQUIRE(pages.size() == 1);

    std::string content = read_page_content(pages.front());
    REQUIRE(content.find(" rg") == std::string::npos);
    REQUIRE(content.find("0.5 0.5 0.5 RG") != std::string::npos);
    REQUIRE(content.find(" k") != std::string::npos);

    auto images = pages.front().getImages();
    REQUIRE(images.contains("/Im1"));
    auto image = images.at("/Im1");
    REQUIRE(image.getDict().getKey("/ColorSpace").isName());
    REQUIRE(image.getDict().getKey("/ColorSpace").getName() == "/DeviceCMYK");
    REQUIRE(read_stream_bytes(image).size() == 4);
}

TEST_CASE("ImageColorConvertFix leaves grayscale images untouched", "[fix][h07]") {
    std::vector<unsigned char> gray_bytes = {0x11, 0x80, 0xF0, 0x55};
    auto input = build_pdf_with_single_page(
        "q\n/Im1 Do\nQ\n",
        [&](QPDF& pdf, QPDFObjectHandle& resources) {
            QPDFObjectHandle xobject = QPDFObjectHandle::newDictionary();
            xobject.replaceKey(
                "/Im1",
                make_image(
                    pdf,
                    2,
                    2,
                    QPDFObjectHandle::newName("/DeviceGray"),
                    gray_bytes));
            resources.replaceKey("/XObject", xobject);
        });

    QPDF pdf;
    pdf.processFile(input.string().c_str());
    std::vector<domain::Finding> findings = {rgb_finding()};
    auto preset = preset_with_profile();
    fix::FixContext ctx{pdf, preset, findings};
    fix::ImageColorConvertFix fix_instance;

    auto record = fix_instance.apply(ctx);
    REQUIRE_FALSE(record.success);
    REQUIRE(record.details.at("images_converted") == "0");

    QPDFPageDocumentHelper helper(pdf);
    auto image = helper.getAllPages().front().getImages().at("/Im1");
    REQUIRE(image.getDict().getKey("/ColorSpace").getName() == "/DeviceGray");
    REQUIRE(read_stream_bytes(image) == gray_bytes);
}

TEST_CASE("RGB image conversion keeps channel relationships visually sane", "[fix][h07]") {
    std::vector<unsigned char> rgb_bytes = {255, 0, 0};
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
                    QPDFObjectHandle::newName("/DeviceRGB"),
                    rgb_bytes));
            resources.replaceKey("/XObject", xobject);
        });

    QPDF pdf;
    pdf.processFile(input.string().c_str());
    std::vector<domain::Finding> findings = {rgb_finding()};
    auto preset = preset_with_profile();
    fix::FixContext ctx{pdf, preset, findings};
    fix::ImageColorConvertFix fix_instance;

    auto record = fix_instance.apply(ctx);
    REQUIRE(record.success);

    auto image = QPDFPageDocumentHelper(pdf).getAllPages().front().getImages().at("/Im1");
    auto cmyk = read_stream_bytes(image);
    REQUIRE(cmyk.size() == 4);
    REQUIRE(cmyk[1] > cmyk[0]);
    REQUIRE(cmyk[2] > cmyk[0]);
    REQUIRE(cmyk[1] > 20);
    REQUIRE(cmyk[2] > 20);
}

TEST_CASE("Large RGB image conversion stays under the performance budget", "[fix][h07]") {
    constexpr int width = 1600;
    constexpr int height = 1600;
    std::vector<unsigned char> rgb_bytes(static_cast<std::size_t>(width) * height * 3U);
    for (std::size_t i = 0; i < rgb_bytes.size(); i += 3U) {
        rgb_bytes[i + 0] = static_cast<unsigned char>((i / 3U) % 255U);
        rgb_bytes[i + 1] = 180;
        rgb_bytes[i + 2] = 60;
    }

    auto input = build_pdf_with_single_page(
        "q\n/Im1 Do\nQ\n",
        [&](QPDF& pdf, QPDFObjectHandle& resources) {
            QPDFObjectHandle xobject = QPDFObjectHandle::newDictionary();
            xobject.replaceKey(
                "/Im1",
                make_image(
                    pdf,
                    width,
                    height,
                    QPDFObjectHandle::newName("/DeviceRGB"),
                    rgb_bytes));
            resources.replaceKey("/XObject", xobject);
        });

    auto output = temp_output_path("printguard_h07_perf");
    auto engine = fix::create_default_fix_engine();
    fix::FixPlanner planner;
    std::vector<domain::Finding> findings = {rgb_finding()};
    auto plan = planner.build_plan(findings, *engine, preset_with_profile());

    auto started = std::chrono::steady_clock::now();
    auto result =
        engine->execute(input.string(), output.string(), plan, findings, preset_with_profile());
    auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::steady_clock::now() - started);

    REQUIRE(result.changes_applied);
    REQUIRE(elapsed.count() < 10);
    require_qpdf_check(output);
}

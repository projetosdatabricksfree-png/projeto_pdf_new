#include <catch2/catch_test_macros.hpp>

#include "printguard/domain/finding.hpp"
#include "printguard/domain/preset.hpp"
#include "printguard/fix/fix_engine.hpp"

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

QPDFObjectHandle make_annotation(QPDF& pdf, const std::string& subtype) {
    QPDFObjectHandle annotation = QPDFObjectHandle::newDictionary();
    annotation.replaceKey("/Type", QPDFObjectHandle::newName("/Annot"));
    annotation.replaceKey("/Subtype", QPDFObjectHandle::newName(subtype));
    annotation.replaceKey("/Rect", make_box_pts(10, 10, 50, 30));
    return pdf.makeIndirectObject(annotation);
}

QPDFObjectHandle make_ocg(QPDF& pdf, const std::string& name) {
    QPDFObjectHandle layer = QPDFObjectHandle::newDictionary();
    layer.replaceKey("/Type", QPDFObjectHandle::newName("/OCG"));
    layer.replaceKey("/Name", QPDFObjectHandle::newString(name));
    return pdf.makeIndirectObject(layer);
}

QPDFObjectHandle make_separation_colorspace() {
    QPDFObjectHandle tint_function = QPDFObjectHandle::newDictionary();
    tint_function.replaceKey("/FunctionType", QPDFObjectHandle::newInteger(2));
    tint_function.replaceKey("/Domain", QPDFObjectHandle::newArray(
        {QPDFObjectHandle::newReal(0.0), QPDFObjectHandle::newReal(1.0)}));
    tint_function.replaceKey("/C0", QPDFObjectHandle::newArray(
        {QPDFObjectHandle::newReal(0.0),
         QPDFObjectHandle::newReal(0.0),
         QPDFObjectHandle::newReal(0.0),
         QPDFObjectHandle::newReal(0.0)}));
    tint_function.replaceKey("/C1", QPDFObjectHandle::newArray(
        {QPDFObjectHandle::newReal(0.0),
         QPDFObjectHandle::newReal(0.5),
         QPDFObjectHandle::newReal(1.0),
         QPDFObjectHandle::newReal(0.0)}));
    tint_function.replaceKey("/N", QPDFObjectHandle::newReal(1.0));

    return QPDFObjectHandle::newArray(
        {QPDFObjectHandle::newName("/Separation"),
         QPDFObjectHandle::newName("/PANTONE_185_C"),
         QPDFObjectHandle::newName("/DeviceCMYK"),
         tint_function});
}

std::filesystem::path build_pdf_with_single_page(
    const std::string& content_stream,
    std::function<void(QPDF&, QPDFObjectHandle& resources)> configure_resources,
    std::function<void(QPDF&, QPDFObjectHandle& page)> configure_page,
    std::function<void(QPDF&)> configure_document = {}) {
    QPDF pdf;
    pdf.emptyPDF();

    QPDFObjectHandle resources = QPDFObjectHandle::newDictionary();
    configure_resources(pdf, resources);

    QPDFObjectHandle contents = pdf.makeIndirectObject(pdf.newStream(content_stream));

    QPDFObjectHandle page = QPDFObjectHandle::newDictionary();
    page.replaceKey("/Type", QPDFObjectHandle::newName("/Page"));
    page.replaceKey("/MediaBox", make_box_pts(0, 0, 200, 300));
    page.replaceKey("/TrimBox", make_box_pts(0, 0, 200, 300));
    page.replaceKey("/Resources", resources);
    page.replaceKey("/Contents", contents);
    configure_page(pdf, page);

    QPDFPageDocumentHelper pdh(pdf);
    pdh.addPage(QPDFPageObjectHelper(page), false);

    if (configure_document) {
        configure_document(pdf);
    }

    static int counter = 0;
    ++counter;
    return write_temp_pdf(pdf, "printguard_h09_" + std::to_string(counter) + ".pdf");
}

std::filesystem::path temp_output_path(const std::string& stem) {
    static int counter = 0;
    ++counter;
    return std::filesystem::temp_directory_path() /
        (stem + "_" + std::to_string(counter) + ".pdf");
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

void require_qpdf_check(const std::filesystem::path& path) {
    std::string command = "qpdf --check \"" + path.string() + "\" > /dev/null 2>&1";
    REQUIRE(std::system(command.c_str()) == 0);
}

domain::Finding finding_for(const std::string& code, int page = 1) {
    return {code, "test", "test", domain::FindingSeverity::WARNING, domain::Fixability::AUTOMATIC_SAFE, page, code, code, {}};
}

domain::ProductPreset portrait_preset() {
    domain::ProductPreset preset;
    preset.orientation = "portrait";
    return preset;
}

} // namespace

TEST_CASE("White overprint is disarmed in page ExtGState", "[fix][h09]") {
    auto input = build_pdf_with_single_page(
        "/GS1 gs\n1 1 1 rg\n0 0 10 10 re f\n",
        [&](QPDF&, QPDFObjectHandle& resources) {
            QPDFObjectHandle ext_gstate = QPDFObjectHandle::newDictionary();
            QPDFObjectHandle state = QPDFObjectHandle::newDictionary();
            state.replaceKey("/OP", QPDFObjectHandle::newBool(true));
            state.replaceKey("/op", QPDFObjectHandle::newBool(true));
            ext_gstate.replaceKey("/GS1", state);
            resources.replaceKey("/ExtGState", ext_gstate);
        },
        [&](QPDF&, QPDFObjectHandle&) {});

    auto output = temp_output_path("printguard_h09_white");
    auto engine = fix::create_default_fix_engine();
    std::vector<domain::Finding> findings = {finding_for("PG_ERR_WHITE_OVERPRINT", 1)};
    fix::FixPlanner planner;
    auto plan = planner.build_plan(findings, *engine, portrait_preset());
    auto result = engine->execute(input.string(), output.string(), plan, findings, portrait_preset());

    REQUIRE(result.changes_applied);
    REQUIRE(std::any_of(result.records.begin(), result.records.end(), [](const domain::FixRecord& record) {
        return record.fix_id == "RemoveWhiteOverprintFix";
    }));
    require_qpdf_check(output);

    QPDF pdf;
    pdf.processFile(output.string().c_str());
    auto page = QPDFPageDocumentHelper(pdf).getAllPages().front();
    QPDFObjectHandle state = page.getAttribute("/Resources", false).getKey("/ExtGState").getKey("/GS1");
    REQUIRE_FALSE(state.getKey("/OP").getBoolValue());
    REQUIRE_FALSE(state.getKey("/op").getBoolValue());
}

TEST_CASE("Annotations are removed while /Link is preserved", "[fix][h09]") {
    auto input = build_pdf_with_single_page(
        "q\nQ\n",
        [&](QPDF&, QPDFObjectHandle&) {},
        [&](QPDF& pdf, QPDFObjectHandle& page) {
            page.replaceKey("/Annots", QPDFObjectHandle::newArray(
                {make_annotation(pdf, "/Text"), make_annotation(pdf, "/Link")}));
        });

    auto output = temp_output_path("printguard_h09_annots");
    auto engine = fix::create_default_fix_engine();
    std::vector<domain::Finding> findings = {finding_for("PG_WARN_ANNOTATIONS", 1)};
    fix::FixPlanner planner;
    auto plan = planner.build_plan(findings, *engine, portrait_preset());
    auto result = engine->execute(input.string(), output.string(), plan, findings, portrait_preset());

    REQUIRE(result.changes_applied);
    require_qpdf_check(output);

    QPDF pdf;
    pdf.processFile(output.string().c_str());
    QPDFObjectHandle annots = QPDFPageDocumentHelper(pdf).getAllPages().front().getObjectHandle().getKey("/Annots");
    REQUIRE(annots.isArray());
    REQUIRE(annots.getArrayNItems() == 1);
    REQUIRE(annots.getArrayItem(0).getKey("/Subtype").getName() == "/Link");
}

TEST_CASE("Layers are flattened without removing visible drawing commands", "[fix][h09]") {
    auto input = build_pdf_with_single_page(
        "/OC /MC0 BDC\n0 0 20 20 re f\nEMC\n",
        [&](QPDF&, QPDFObjectHandle& resources) {
            QPDFObjectHandle properties = QPDFObjectHandle::newDictionary();
            QPDFObjectHandle layer = QPDFObjectHandle::newDictionary();
            layer.replaceKey("/Type", QPDFObjectHandle::newName("/OCG"));
            layer.replaceKey("/Name", QPDFObjectHandle::newString("Layer 1"));
            properties.replaceKey("/MC0", layer);
            resources.replaceKey("/Properties", properties);
        },
        [&](QPDF&, QPDFObjectHandle&) {},
        [&](QPDF& pdf) {
            QPDFObjectHandle layer = make_ocg(pdf, "Layer 1");
            QPDFObjectHandle oc_properties = QPDFObjectHandle::newDictionary();
            oc_properties.replaceKey("/OCGs", QPDFObjectHandle::newArray({layer}));
            oc_properties.replaceKey("/D", QPDFObjectHandle::newDictionary());
            pdf.getRoot().replaceKey("/OCProperties", oc_properties);
        });

    auto output = temp_output_path("printguard_h09_layers");
    auto engine = fix::create_default_fix_engine();
    std::vector<domain::Finding> findings = {finding_for("PG_WARN_LAYERS_PRESENT", 0)};
    fix::FixPlanner planner;
    auto plan = planner.build_plan(findings, *engine, portrait_preset());
    auto result = engine->execute(input.string(), output.string(), plan, findings, portrait_preset());

    REQUIRE(result.changes_applied);
    require_qpdf_check(output);

    QPDF pdf;
    pdf.processFile(output.string().c_str());
    REQUIRE_FALSE(pdf.getRoot().hasKey("/OCProperties"));
    auto page = QPDFPageDocumentHelper(pdf).getAllPages().front();
    auto resources = page.getAttribute("/Resources", false);
    REQUIRE_FALSE(resources.hasKey("/Properties"));
    std::string content = read_page_content(page);
    REQUIRE(content.find("0 0 20 20 re f") != std::string::npos);
    REQUIRE(content.find("BDC") == std::string::npos);
    REQUIRE(content.find("EMC") == std::string::npos);
}

TEST_CASE("Simple spot Separation is converted to CMYK", "[fix][h09]") {
    auto input = build_pdf_with_single_page(
        "/CS1 cs\n0.5 scn\n",
        [&](QPDF&, QPDFObjectHandle& resources) {
            QPDFObjectHandle color_spaces = QPDFObjectHandle::newDictionary();
            color_spaces.replaceKey("/CS1", make_separation_colorspace());
            resources.replaceKey("/ColorSpace", color_spaces);
        },
        [&](QPDF&, QPDFObjectHandle&) {});

    auto output = temp_output_path("printguard_h09_spot");
    auto engine = fix::create_default_fix_engine();
    std::vector<domain::Finding> findings = {finding_for("PG_WARN_SPOT_COLORS", 1)};
    fix::FixPlanner planner;
    auto plan = planner.build_plan(findings, *engine, portrait_preset());
    auto result = engine->execute(input.string(), output.string(), plan, findings, portrait_preset());

    REQUIRE(result.changes_applied);
    require_qpdf_check(output);

    QPDF pdf;
    pdf.processFile(output.string().c_str());
    auto page = QPDFPageDocumentHelper(pdf).getAllPages().front();
    QPDFObjectHandle color_space = page.getAttribute("/Resources", false).getKey("/ColorSpace").getKey("/CS1");
    REQUIRE(color_space.isName());
    REQUIRE(color_space.getName() == "/DeviceCMYK");
    std::string content = read_page_content(page);
    REQUIRE(content.find("0.0000 0.2500 0.5000 0.0000 k") != std::string::npos);
}

TEST_CASE("Rotation fix only adjusts /Rotate to match product orientation", "[fix][h09]") {
    auto input = build_pdf_with_single_page(
        "q\nQ\n",
        [&](QPDF&, QPDFObjectHandle&) {},
        [&](QPDF&, QPDFObjectHandle&) {});

    auto output = temp_output_path("printguard_h09_rotation");
    auto engine = fix::create_default_fix_engine();
    domain::ProductPreset preset;
    preset.orientation = "landscape";
    std::vector<domain::Finding> findings = {finding_for("PG_WARN_ROTATION_MISMATCH", 1)};
    fix::FixPlanner planner;
    auto plan = planner.build_plan(findings, *engine, preset);
    auto result = engine->execute(input.string(), output.string(), plan, findings, preset);

    REQUIRE(result.changes_applied);
    require_qpdf_check(output);

    QPDF pdf;
    pdf.processFile(output.string().c_str());
    auto page = QPDFPageDocumentHelper(pdf).getAllPages().front();
    REQUIRE(page.getAttribute("/Rotate", false).getIntValueAsInt() == 90);
}

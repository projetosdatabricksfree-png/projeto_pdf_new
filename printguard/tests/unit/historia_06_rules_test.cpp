#include <catch2/catch_test_macros.hpp>

#include "printguard/analysis/rule_interface.hpp"
#include "printguard/analysis/rules/annotation_rule.hpp"
#include "printguard/analysis/rules/layer_rule.hpp"
#include "printguard/analysis/rules/rotation_rule.hpp"
#include "printguard/analysis/rules/spot_color_rule.hpp"
#include "printguard/domain/preset.hpp"
#include "printguard/domain/profile.hpp"
#include "printguard/pdf/pdf_loader.hpp"

#include <filesystem>
#include <functional>
#include <qpdf/QPDF.hh>
#include <qpdf/QPDFObjectHandle.hh>
#include <qpdf/QPDFPageDocumentHelper.hh>
#include <qpdf/QPDFPageObjectHelper.hh>
#include <qpdf/QPDFWriter.hh>

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

QPDFObjectHandle make_annotation(QPDF& pdf, std::string const& subtype) {
    QPDFObjectHandle annotation = QPDFObjectHandle::newDictionary();
    annotation.replaceKey("/Type", QPDFObjectHandle::newName("/Annot"));
    annotation.replaceKey("/Subtype", QPDFObjectHandle::newName(subtype));
    annotation.replaceKey("/Rect", make_box_pts(10, 10, 50, 30));
    return pdf.makeIndirectObject(annotation);
}

QPDFObjectHandle make_ocg(QPDF& pdf, std::string const& name) {
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
    std::string const& content_stream,
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
    return write_temp_pdf(pdf, "printguard_h06_" + std::to_string(counter) + ".pdf");
}

domain::ValidationProfile profile_with_rule(
    std::string const& rule_id,
    domain::RuleSeverity severity,
    bool enabled) {
    domain::ValidationProfile p;
    p.id = "test";
    p.name = "test";
    p.description = "test";
    p.rules[rule_id] = domain::RuleConfig{enabled, severity, {}};
    return p;
}

} // namespace

TEST_CASE("AnnotationRule detects non-link annotations and ignores links", "[analysis][h06][annotations]") {
    auto path = build_pdf_with_single_page(
        "q\nQ\n",
        [&](QPDF&, QPDFObjectHandle&) {},
        [&](QPDF& pdf, QPDFObjectHandle& page) {
            QPDFObjectHandle annots = QPDFObjectHandle::newArray(
                {make_annotation(pdf, "/Text"), make_annotation(pdf, "/Link")});
            page.replaceKey("/Annots", annots);
        });

    domain::ProductPreset preset;
    auto profile = profile_with_rule("annotations", domain::RuleSeverity::WARNING, true);

    analysis::AnnotationRule rule;
    QPDF pdf;
    pdf::DocumentModel model;
    pdf.processFile(path.string().c_str());
    model = pdf::PdfLoader::load_from_file(path.string());
    analysis::RuleContext ctx{pdf, model, preset, profile};
    auto findings = rule.evaluate(ctx);

    REQUIRE(findings.size() == 1);
    REQUIRE(findings[0].code == "PG_WARN_ANNOTATIONS");
    REQUIRE(findings[0].evidence.at("annotation_count") == "1");
    REQUIRE(findings[0].evidence.at("annotation_types") == "Text");
}

TEST_CASE("LayerRule detects OCProperties", "[analysis][h06][layers]") {
    auto path = build_pdf_with_single_page(
        "q\nQ\n",
        [&](QPDF&, QPDFObjectHandle&) {},
        [&](QPDF&, QPDFObjectHandle&) {},
        [&](QPDF& pdf) {
            QPDFObjectHandle layer = make_ocg(pdf, "Layer 1");
            QPDFObjectHandle ocgs = QPDFObjectHandle::newArray({layer});
            QPDFObjectHandle default_config = QPDFObjectHandle::newDictionary();
            default_config.replaceKey("/Order", QPDFObjectHandle::newArray({layer}));

            QPDFObjectHandle oc_properties = QPDFObjectHandle::newDictionary();
            oc_properties.replaceKey("/OCGs", ocgs);
            oc_properties.replaceKey("/D", default_config);
            pdf.getRoot().replaceKey("/OCProperties", oc_properties);
        });

    domain::ProductPreset preset;
    auto profile = profile_with_rule("layers", domain::RuleSeverity::WARNING, true);

    analysis::LayerRule rule;
    QPDF pdf;
    pdf::DocumentModel model;
    pdf.processFile(path.string().c_str());
    model = pdf::PdfLoader::load_from_file(path.string());
    analysis::RuleContext ctx{pdf, model, preset, profile};
    auto findings = rule.evaluate(ctx);

    REQUIRE(findings.size() == 1);
    REQUIRE(findings[0].code == "PG_WARN_LAYERS_PRESENT");
    REQUIRE(findings[0].evidence.at("layer_count") == "1");
    REQUIRE(findings[0].evidence.at("layer_names") == "Layer 1");
}

TEST_CASE("SpotColorRule detects Separation when spot colors are forbidden", "[analysis][h06][spot_colors]") {
    auto path = build_pdf_with_single_page(
        "q\nQ\n",
        [&](QPDF&, QPDFObjectHandle& resources) {
            QPDFObjectHandle color_spaces = QPDFObjectHandle::newDictionary();
            color_spaces.replaceKey("/CS1", make_separation_colorspace());
            resources.replaceKey("/ColorSpace", color_spaces);
        },
        [&](QPDF&, QPDFObjectHandle&) {});

    domain::ProductPreset preset;
    preset.color_policy.allow_spot_colors = false;

    auto profile = profile_with_rule("spot_colors", domain::RuleSeverity::WARNING, true);

    analysis::SpotColorRule rule;
    QPDF pdf;
    pdf::DocumentModel model;
    pdf.processFile(path.string().c_str());
    model = pdf::PdfLoader::load_from_file(path.string());
    analysis::RuleContext ctx{pdf, model, preset, profile};
    auto findings = rule.evaluate(ctx);

    REQUIRE(findings.size() == 1);
    REQUIRE(findings[0].code == "PG_WARN_SPOT_COLORS");
    REQUIRE(findings[0].evidence.at("spot_color_names") == "PANTONE_185_C");
}

TEST_CASE("RotationRule detects incorrect orientation", "[analysis][h06][rotation]") {
    auto path = build_pdf_with_single_page(
        "q\nQ\n",
        [&](QPDF&, QPDFObjectHandle&) {},
        [&](QPDF&, QPDFObjectHandle&) {});

    domain::ProductPreset preset;
    preset.orientation = "landscape";

    auto profile = profile_with_rule("rotation", domain::RuleSeverity::WARNING, true);

    analysis::RotationRule rule;
    QPDF pdf;
    pdf::DocumentModel model;
    pdf.processFile(path.string().c_str());
    model = pdf::PdfLoader::load_from_file(path.string());
    analysis::RuleContext ctx{pdf, model, preset, profile};
    auto findings = rule.evaluate(ctx);

    REQUIRE(findings.size() == 1);
    REQUIRE(findings[0].code == "PG_WARN_ROTATION_MISMATCH");
    REQUIRE(findings[0].evidence.at("expected_orientation") == "landscape");
}

TEST_CASE("RotationRule skips findings when preset orientation is either", "[analysis][h06][rotation]") {
    auto path = build_pdf_with_single_page(
        "q\nQ\n",
        [&](QPDF&, QPDFObjectHandle&) {},
        [&](QPDF&, QPDFObjectHandle&) {});

    domain::ProductPreset preset;
    preset.orientation = "either";

    auto profile = profile_with_rule("rotation", domain::RuleSeverity::WARNING, true);

    analysis::RotationRule rule;
    QPDF pdf;
    pdf::DocumentModel model;
    pdf.processFile(path.string().c_str());
    model = pdf::PdfLoader::load_from_file(path.string());
    analysis::RuleContext ctx{pdf, model, preset, profile};
    auto findings = rule.evaluate(ctx);

    REQUIRE(findings.empty());
}

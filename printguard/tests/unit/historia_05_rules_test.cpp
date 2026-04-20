#include <catch2/catch_test_macros.hpp>

#include "printguard/analysis/rule_interface.hpp"
#include "printguard/analysis/rules/black_consistency_rule.hpp"
#include "printguard/analysis/rules/output_intent_rule.hpp"
#include "printguard/analysis/rules/tac_rule.hpp"
#include "printguard/analysis/rules/white_overprint_rule.hpp"
#include "printguard/analysis/rules/safety_margin_rule.hpp"
#include "printguard/domain/preset.hpp"
#include "printguard/domain/profile.hpp"
#include "printguard/pdf/pdf_loader.hpp"

#include <functional>
#include <filesystem>
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

QPDFObjectHandle make_type1_font(QPDF& pdf) {
    QPDFObjectHandle font = QPDFObjectHandle::newDictionary();
    font.replaceKey("/Type", QPDFObjectHandle::newName("/Font"));
    font.replaceKey("/Subtype", QPDFObjectHandle::newName("/Type1"));
    font.replaceKey("/BaseFont", QPDFObjectHandle::newName("/Helvetica"));
    return pdf.makeIndirectObject(font);
}

QPDFObjectHandle make_extgstate_overprint(QPDF& pdf) {
    QPDFObjectHandle gs = QPDFObjectHandle::newDictionary();
    gs.replaceKey("/OP", QPDFObjectHandle::newBool(true));
    gs.replaceKey("/op", QPDFObjectHandle::newBool(true));
    return pdf.makeIndirectObject(gs);
}

QPDFObjectHandle make_cmyk_image(QPDF& pdf, int width, int height, std::string const& raw) {
    QPDFObjectHandle image = pdf.newStream(raw);
    QPDFObjectHandle dict = image.getDict();
    dict.replaceKey("/Type", QPDFObjectHandle::newName("/XObject"));
    dict.replaceKey("/Subtype", QPDFObjectHandle::newName("/Image"));
    dict.replaceKey("/Width", QPDFObjectHandle::newInteger(width));
    dict.replaceKey("/Height", QPDFObjectHandle::newInteger(height));
    dict.replaceKey("/ColorSpace", QPDFObjectHandle::newName("/DeviceCMYK"));
    dict.replaceKey("/BitsPerComponent", QPDFObjectHandle::newInteger(8));
    return pdf.makeIndirectObject(image);
}

std::filesystem::path build_pdf_with_single_page(
    std::string const& content_stream,
    std::function<void(QPDF&, QPDFObjectHandle& resources)> configure_resources,
    std::function<void(QPDF&, QPDFObjectHandle& page)> configure_page) {
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
    configure_page(pdf, page);

    QPDFPageDocumentHelper pdh(pdf);
    pdh.addPage(QPDFPageObjectHelper(page), false);

    static int counter = 0;
    ++counter;
    return write_temp_pdf(pdf, "printguard_h05_" + std::to_string(counter) + ".pdf");
}

domain::ValidationProfile profile_with_rule(
    std::string const& rule_id,
    domain::RuleSeverity severity,
    bool enabled,
    std::map<std::string, std::string> params = {}) {
    domain::ValidationProfile p;
    p.id = "test";
    p.name = "test";
    p.description = "test";
    p.rules[rule_id] = domain::RuleConfig{enabled, severity, std::move(params)};
    return p;
}

} // namespace

TEST_CASE("TacRule detects TAC above limit", "[analysis][h05][tac]") {
    std::string raw(4 * 4, static_cast<char>(0xFF)); // 1px = 4 bytes; 2x2 = 16 bytes, TAC=400%
    auto path = build_pdf_with_single_page(
        "q\n1 0 0 1 0 0 cm\n/Im1 Do\nQ\n",
        [&](QPDF& pdf, QPDFObjectHandle& resources) {
            QPDFObjectHandle xobj = QPDFObjectHandle::newDictionary();
            xobj.replaceKey("/Im1", make_cmyk_image(pdf, 2, 2, raw));
            resources.replaceKey("/XObject", xobj);
        },
        [&](QPDF&, QPDFObjectHandle&) {});

    domain::ProductPreset preset;
    preset.max_total_ink_percent = 320;

    auto profile = profile_with_rule("tac", domain::RuleSeverity::ERROR, true, {{"max_tac_percent", "320"}, {"sample_step", "1"}});

    analysis::TacRule rule;
    QPDF pdf;
    pdf.processFile(path.string().c_str());
    auto model = pdf::PdfLoader::load_from_file(path.string());
    analysis::RuleContext ctx{pdf, model, preset, profile};
    auto findings = rule.evaluate(ctx);

    REQUIRE_FALSE(findings.empty());
    REQUIRE(findings[0].code == "PG_ERR_TAC_EXCEEDED");
}

TEST_CASE("OutputIntentRule detects missing output intent when required", "[analysis][h05][output_intent]") {
    auto path = build_pdf_with_single_page(
        "q\nQ\n",
        [&](QPDF&, QPDFObjectHandle&) {},
        [&](QPDF&, QPDFObjectHandle&) {});

    domain::ProductPreset preset;
    preset.color_policy.require_output_intent = true;

    auto profile = profile_with_rule("output_intent", domain::RuleSeverity::ERROR, true);

    analysis::OutputIntentRule rule;
    QPDF pdf;
    pdf.processFile(path.string().c_str());
    auto model = pdf::PdfLoader::load_from_file(path.string());
    analysis::RuleContext ctx{pdf, model, preset, profile};
    auto findings = rule.evaluate(ctx);

    REQUIRE(findings.size() == 1);
    REQUIRE(findings[0].code == "PG_ERR_MISSING_OUTPUT_INTENT");
}

TEST_CASE("WhiteOverprintRule detects white overprint when forbidden", "[analysis][h05][white_overprint]") {
    auto path = build_pdf_with_single_page(
        "q\n/GS1 gs\n0 0 0 0 k\n0 0 m\n10 0 l\nS\nQ\n",
        [&](QPDF& pdf, QPDFObjectHandle& resources) {
            QPDFObjectHandle ext = QPDFObjectHandle::newDictionary();
            ext.replaceKey("/GS1", make_extgstate_overprint(pdf));
            resources.replaceKey("/ExtGState", ext);
        },
        [&](QPDF&, QPDFObjectHandle&) {});

    domain::ProductPreset preset;
    preset.text_policy.forbid_white_overprint = true;

    auto profile = profile_with_rule("white_overprint", domain::RuleSeverity::ERROR, true);

    analysis::WhiteOverprintRule rule;
    QPDF pdf;
    pdf.processFile(path.string().c_str());
    auto model = pdf::PdfLoader::load_from_file(path.string());
    analysis::RuleContext ctx{pdf, model, preset, profile};
    auto findings = rule.evaluate(ctx);

    REQUIRE_FALSE(findings.empty());
    REQUIRE(findings[0].code == "PG_ERR_WHITE_OVERPRINT");
}

TEST_CASE("BlackConsistencyRule detects rich black in text blocks", "[analysis][h05][black_consistency]") {
    auto path = build_pdf_with_single_page(
        "BT\n/F1 12 Tf\n0.2 0.1 0.1 1 k\n72 720 Td\n(Hello) Tj\nET\n",
        [&](QPDF& pdf, QPDFObjectHandle& resources) {
            QPDFObjectHandle fonts = QPDFObjectHandle::newDictionary();
            fonts.replaceKey("/F1", make_type1_font(pdf));
            resources.replaceKey("/Font", fonts);
        },
        [&](QPDF&, QPDFObjectHandle&) {});

    domain::ProductPreset preset;
    preset.text_policy.normalize_rich_black_small_text = true;

    auto profile = profile_with_rule("black_consistency", domain::RuleSeverity::WARNING, true);

    analysis::BlackConsistencyRule rule;
    QPDF pdf;
    pdf.processFile(path.string().c_str());
    auto model = pdf::PdfLoader::load_from_file(path.string());
    analysis::RuleContext ctx{pdf, model, preset, profile};
    auto findings = rule.evaluate(ctx);

    REQUIRE_FALSE(findings.empty());
    REQUIRE(findings[0].code == "PG_WARN_RICH_BLACK_TEXT");
}

TEST_CASE("SafetyMarginRule uses preset.safe_margin_mm and skips when zero", "[analysis][h05][safety_margin]") {
    auto path = build_pdf_with_single_page(
        "BT\n1 0 0 1 1 1 Tm\n(Hi) Tj\nET\n",
        [&](QPDF& pdf, QPDFObjectHandle& resources) {
            QPDFObjectHandle fonts = QPDFObjectHandle::newDictionary();
            fonts.replaceKey("/F1", make_type1_font(pdf));
            resources.replaceKey("/Font", fonts);
        },
        [&](QPDF&, QPDFObjectHandle&) {});

    domain::ValidationProfile profile;
    profile.id = "test";
    profile.name = "test";
    profile.description = "test";

    {
        domain::ProductPreset preset;
        preset.safe_margin_mm = 5.0;
        analysis::SafetyMarginRule rule;
        QPDF pdf;
        pdf.processFile(path.string().c_str());
        auto model = pdf::PdfLoader::load_from_file(path.string());
        analysis::RuleContext ctx{pdf, model, preset, profile};
        auto findings = rule.evaluate(ctx);
        REQUIRE_FALSE(findings.empty());
        REQUIRE(findings[0].code == "PG_ERR_SAFETY_MARGIN");
    }

    {
        domain::ProductPreset preset;
        preset.safe_margin_mm = 0.0;
        analysis::SafetyMarginRule rule;
        QPDF pdf;
        pdf.processFile(path.string().c_str());
        auto model = pdf::PdfLoader::load_from_file(path.string());
        analysis::RuleContext ctx{pdf, model, preset, profile};
        auto findings = rule.evaluate(ctx);
        REQUIRE(findings.empty());
    }
}

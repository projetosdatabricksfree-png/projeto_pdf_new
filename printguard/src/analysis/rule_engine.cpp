#include "printguard/analysis/rule_engine.hpp"

#include "printguard/common/logging.hpp"
#include "printguard/pdf/pdf_loader.hpp"
#include "printguard/analysis/rules/page_geometry_rule.hpp"
#include "printguard/analysis/rules/bleed_rule.hpp"
#include "printguard/analysis/rules/color_space_rule.hpp"
#include "printguard/analysis/rules/image_resolution_rule.hpp"
#include "printguard/analysis/rules/safety_margin_rule.hpp"
#include "printguard/analysis/rules/tac_rule.hpp"
#include "printguard/analysis/rules/output_intent_rule.hpp"
#include "printguard/analysis/rules/white_overprint_rule.hpp"
#include "printguard/analysis/rules/black_consistency_rule.hpp"
#include "printguard/analysis/rules/annotation_rule.hpp"
#include "printguard/analysis/rules/layer_rule.hpp"
#include "printguard/analysis/rules/spot_color_rule.hpp"
#include "printguard/analysis/rules/rotation_rule.hpp"
#include "printguard/analysis/rules/transparency_rule.hpp"
#include <qpdf/QPDF.hh>

namespace printguard::analysis {

void RuleEngine::register_rule(std::unique_ptr<IRule> rule) {
    m_rules.push_back(std::move(rule));
}

AnalysisResult RuleEngine::run(
    const std::string& pdf_path,
    const domain::ProductPreset& preset,
    const domain::ValidationProfile& profile) const {
    AnalysisResult result;
    result.document = pdf::PdfLoader::load_from_file(pdf_path);

    QPDF pdf;
    pdf.processFile(pdf_path.c_str());

    RuleContext context{
        pdf,
        result.document,
        preset,
        profile};

    for (const auto& rule : m_rules) {
        auto rule_id = rule->id();
        auto rule_config = profile.rules.find(rule_id);

        if (rule_config != profile.rules.end() && !rule_config->second.enabled) {
            continue;
        }

        auto findings = rule->evaluate(context);
        result.findings.insert(result.findings.end(), findings.begin(), findings.end());
    }

    return result;
}

std::unique_ptr<RuleEngine> create_default_engine() {
    auto engine = std::make_unique<RuleEngine>();
    engine->register_rule(std::make_unique<PageGeometryRule>());
    engine->register_rule(std::make_unique<BleedRule>());
    engine->register_rule(std::make_unique<ColorSpaceRule>());
    engine->register_rule(std::make_unique<ImageResolutionRule>());
    engine->register_rule(std::make_unique<SafetyMarginRule>());
    engine->register_rule(std::make_unique<TransparencyRule>());
    engine->register_rule(std::make_unique<TacRule>());
    engine->register_rule(std::make_unique<OutputIntentRule>());
    engine->register_rule(std::make_unique<WhiteOverprintRule>());
    engine->register_rule(std::make_unique<BlackConsistencyRule>());
    engine->register_rule(std::make_unique<AnnotationRule>());
    engine->register_rule(std::make_unique<LayerRule>());
    engine->register_rule(std::make_unique<SpotColorRule>());
    engine->register_rule(std::make_unique<RotationRule>());
    return engine;
}

} // namespace printguard::analysis

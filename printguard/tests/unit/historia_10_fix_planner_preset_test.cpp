#include <catch2/catch_test_macros.hpp>

#include "printguard/domain/finding.hpp"
#include "printguard/domain/preset.hpp"
#include "printguard/fix/fix_engine.hpp"
#include "printguard/fix/fix_interface.hpp"

#include <algorithm>
#include <memory>
#include <string>
#include <vector>

using namespace printguard;

namespace {

class DummyFix final : public fix::IFix {
public:
    DummyFix(std::string fix_id, std::string finding_code) :
        m_fix_id(std::move(fix_id)),
        m_finding_code(std::move(finding_code)) {}

    std::string id() const override {
        return m_fix_id;
    }

    std::string targets_finding_code() const override {
        return m_finding_code;
    }

    domain::FixRecord apply(fix::FixContext&) const override {
        return {m_fix_id, m_finding_code, false, false, "skipped", "dummy", {}};
    }

private:
    std::string m_fix_id;
    std::string m_finding_code;
};

domain::Finding make_finding(
    std::string code,
    domain::FindingSeverity severity,
    domain::Fixability fixability,
    std::string message = {}) {
    return {
        std::move(code),
        "test_rule",
        "test",
        severity,
        fixability,
        1,
        message.empty() ? "technical message" : message,
        message.empty() ? "user message" : message,
        {}};
}

bool contains(std::vector<std::string> const& values, std::string const& expected) {
    return std::find(values.begin(), values.end(), expected) != values.end();
}

bool contains_fragment(std::vector<std::string> const& values, std::string const& fragment) {
    return std::any_of(values.begin(), values.end(), [&](std::string const& value) {
        return value.find(fragment) != std::string::npos;
    });
}

domain::ProductPreset default_preset() {
    return {};
}

} // namespace

TEST_CASE("Planner skips RGB fixes when preset disables RGB auto-fix", "[fix][h10]") {
    auto engine = fix::create_default_fix_engine();
    fix::FixPlanner planner;
    auto preset = default_preset();
    preset.fix_policy.auto_fix_rgb_to_cmyk = false;

    std::vector<domain::Finding> findings = {
        make_finding("PG_ERR_RGB_COLORSPACE", domain::FindingSeverity::ERROR, domain::Fixability::AUTOMATIC_SAFE)};

    auto plan = planner.build_plan(findings, *engine, preset);

    REQUIRE_FALSE(contains(plan.actions, "ConvertRgbToCmykFix"));
    REQUIRE_FALSE(contains(plan.actions, "ImageColorConvertFix"));
    REQUIRE(contains(plan.unresolved_finding_codes, "PG_ERR_RGB_COLORSPACE"));
    REQUIRE(contains_fragment(plan.skipped_fixes, "PG_ERR_RGB_COLORSPACE"));
    REQUIRE(plan.needs_manual_review == false);
    REQUIRE(plan.status == "completed");
}

TEST_CASE("Planner includes RGB fixes when preset enables RGB auto-fix", "[fix][h10]") {
    auto engine = fix::create_default_fix_engine();
    fix::FixPlanner planner;
    auto preset = default_preset();
    preset.fix_policy.auto_fix_rgb_to_cmyk = true;

    std::vector<domain::Finding> findings = {
        make_finding("PG_ERR_RGB_COLORSPACE", domain::FindingSeverity::ERROR, domain::Fixability::AUTOMATIC_SAFE)};

    auto plan = planner.build_plan(findings, *engine, preset);

    REQUIRE(contains(plan.actions, "ConvertRgbToCmykFix"));
    REQUIRE(contains(plan.actions, "ImageColorConvertFix"));
    REQUIRE_FALSE(contains(plan.unresolved_finding_codes, "PG_ERR_RGB_COLORSPACE"));
    REQUIRE(plan.status == "completed");
}

TEST_CASE("Blocking finding without fix requires manual review", "[fix][h10]") {
    fix::FixEngine engine;
    fix::FixPlanner planner;
    auto preset = default_preset();

    std::vector<domain::Finding> findings = {
        make_finding("PG_ERR_UNKNOWN_BLOCKER", domain::FindingSeverity::ERROR, domain::Fixability::NONE)};

    auto plan = planner.build_plan(findings, engine, preset);

    REQUIRE(plan.needs_manual_review);
    REQUIRE(plan.has_blocking_unresolved);
    REQUIRE(plan.status == "manual_review_required");
    REQUIRE(contains(plan.unresolved_finding_codes, "PG_ERR_UNKNOWN_BLOCKER"));
    REQUIRE(contains_fragment(plan.manual_review_reasons, "sem correcao automatica segura"));
}

TEST_CASE("Document preset with bleed zero does not request manual review for bleed", "[fix][h10]") {
    fix::FixEngine engine;
    fix::FixPlanner planner;
    auto preset = default_preset();
    preset.bleed_mm = 0.0;

    std::vector<domain::Finding> findings = {
        make_finding("PG_ERR_BLEED_INSUFFICIENT", domain::FindingSeverity::ERROR, domain::Fixability::NONE)};

    auto plan = planner.build_plan(findings, engine, preset);

    REQUIRE_FALSE(plan.needs_manual_review);
    REQUIRE(plan.has_blocking_unresolved);
    REQUIRE(plan.status == "completed");
    REQUIRE_FALSE(contains_fragment(plan.manual_review_reasons, "bleed"));
}

TEST_CASE("Safety margin manual review policy is respected", "[fix][h10]") {
    fix::FixEngine engine;
    fix::FixPlanner planner;
    auto preset = default_preset();
    preset.manual_review_policy.manual_review_on_safety_margin_violation = false;

    std::vector<domain::Finding> findings = {
        make_finding("PG_ERR_SAFETY_MARGIN", domain::FindingSeverity::ERROR, domain::Fixability::NONE)};

    auto plan = planner.build_plan(findings, engine, preset);

    REQUIRE_FALSE(plan.needs_manual_review);
    REQUIRE(plan.has_blocking_unresolved);
    REQUIRE(plan.status == "completed");
}

TEST_CASE("Complex transparency manual review policy is respected", "[fix][h10]") {
    fix::FixEngine engine;
    fix::FixPlanner planner;
    auto preset = default_preset();
    preset.manual_review_policy.manual_review_on_complex_transparency = true;

    std::vector<domain::Finding> findings = {
        make_finding("PG_WARN_TRANSPARENCY", domain::FindingSeverity::WARNING, domain::Fixability::NONE)};

    auto plan = planner.build_plan(findings, engine, preset);

    REQUIRE(plan.needs_manual_review);
    REQUIRE(plan.status == "manual_review_required");
    REQUIRE(contains_fragment(plan.manual_review_reasons, "Transparencia complexa"));
}

TEST_CASE("Low resolution error respects manual review policy", "[fix][h10]") {
    fix::FixEngine engine;
    fix::FixPlanner planner;
    auto preset = default_preset();
    preset.manual_review_policy.manual_review_on_low_resolution_below_error = true;

    std::vector<domain::Finding> findings = {
        make_finding("PG_ERR_LOW_RES", domain::FindingSeverity::ERROR, domain::Fixability::NONE)};

    auto plan = planner.build_plan(findings, engine, preset);

    REQUIRE(plan.needs_manual_review);
    REQUIRE(plan.has_blocking_unresolved);
    REQUIRE(plan.status == "manual_review_required");
    REQUIRE(contains_fragment(plan.manual_review_reasons, "Resolucao abaixo do minimo"));
}

TEST_CASE("Non-blocking unresolved findings keep completed status", "[fix][h10]") {
    fix::FixEngine engine;
    fix::FixPlanner planner;
    auto preset = default_preset();

    std::vector<domain::Finding> findings = {
        make_finding("PG_WARN_LAYOUT_ODDITY", domain::FindingSeverity::WARNING, domain::Fixability::NONE)};

    auto plan = planner.build_plan(findings, engine, preset);

    REQUIRE_FALSE(plan.needs_manual_review);
    REQUIRE_FALSE(plan.has_blocking_unresolved);
    REQUIRE(plan.status == "completed");
    REQUIRE(contains(plan.unresolved_finding_codes, "PG_WARN_LAYOUT_ODDITY"));
}

TEST_CASE("Planner deduplicates actions and unresolved codes", "[fix][h10]") {
    fix::FixEngine engine;
    engine.register_fix(std::make_unique<DummyFix>("DummyRgbFixA", "PG_ERR_RGB_COLORSPACE"));
    engine.register_fix(std::make_unique<DummyFix>("DummyRgbFixB", "PG_ERR_RGB_COLORSPACE"));
    fix::FixPlanner planner;
    auto preset = default_preset();
    preset.fix_policy.auto_fix_rgb_to_cmyk = true;

    std::vector<domain::Finding> findings = {
        make_finding("PG_ERR_RGB_COLORSPACE", domain::FindingSeverity::ERROR, domain::Fixability::AUTOMATIC_SAFE),
        make_finding("PG_ERR_RGB_COLORSPACE", domain::FindingSeverity::ERROR, domain::Fixability::AUTOMATIC_SAFE),
        make_finding("PG_WARN_LAYOUT_ODDITY", domain::FindingSeverity::WARNING, domain::Fixability::NONE),
        make_finding("PG_WARN_LAYOUT_ODDITY", domain::FindingSeverity::WARNING, domain::Fixability::NONE)};

    auto plan = planner.build_plan(findings, engine, preset);

    REQUIRE(plan.actions.size() == 2);
    REQUIRE(contains(plan.actions, "DummyRgbFixA"));
    REQUIRE(contains(plan.actions, "DummyRgbFixB"));
    REQUIRE(plan.unresolved_finding_codes.size() == 1);
    REQUIRE(plan.unresolved_finding_codes.front() == "PG_WARN_LAYOUT_ODDITY");
}

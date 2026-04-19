#include <catch2/catch_test_macros.hpp>
#include "printguard/common/logging.hpp"

TEST_CASE("Smoke Test: Environment is sane", "[smoke]") {
    REQUIRE(1 == 1);
}

TEST_CASE("Smoke Test: Logger initialization", "[smoke]") {
    // Should not throw
    REQUIRE_NOTHROW(printguard::common::Logger::init("test-suite"));
}

#include <catch2/catch_test_macros.hpp>
#include "printguard/domain/state_machine.hpp"
#include "printguard/domain/config_loader.hpp"

using namespace printguard::domain;

TEST_CASE("StateMachine: Valid transitions", "[domain]") {
    REQUIRE(JobStateMachine::can_transition(JobStatus::UPLOADED, JobStatus::QUEUED));
    REQUIRE(JobStateMachine::can_transition(JobStatus::QUEUED, JobStatus::PARSING));
    REQUIRE(JobStateMachine::can_transition(JobStatus::ANALYZING, JobStatus::FIXING));
    REQUIRE(JobStateMachine::can_transition(JobStatus::ANALYZING, JobStatus::COMPLETED));
}

TEST_CASE("StateMachine: Invalid transitions", "[domain]") {
    REQUIRE_FALSE(JobStateMachine::can_transition(JobStatus::UPLOADED, JobStatus::COMPLETED));
    REQUIRE_FALSE(JobStateMachine::can_transition(JobStatus::COMPLETED, JobStatus::QUEUED));
}

TEST_CASE("StateMachine: Conversion to string", "[domain]") {
    REQUIRE(JobStateMachine::status_to_string(JobStatus::UPLOADED) == "uploaded");
    REQUIRE(JobStateMachine::string_to_status("uploaded") == JobStatus::UPLOADED);
}

enable_testing()

add_executable(unit_tests
    unit/smoke_test.cpp
    unit/domain_test.cpp
    unit/preset_schema_test.cpp
    unit/pdf_test.cpp
    unit/historia_05_rules_test.cpp
    unit/historia_06_rules_test.cpp
    unit/historia_07_fix_rgb_cmyk_lcms2_test.cpp
    unit/historia_08_fixes_intent_tac_preto_test.cpp
    unit/historia_09_fixes_limpeza_test.cpp
    unit/historia_10_fix_planner_preset_test.cpp
    unit/historia_11_pipeline_completo_test.cpp
)

add_dependencies(unit_tests printguard-cli)

target_compile_definitions(unit_tests PRIVATE
    PRINTGUARD_TEST_CLI_PATH="$<TARGET_FILE:printguard-cli>"
    PRINTGUARD_TEST_PROJECT_SOURCE_DIR="${CMAKE_SOURCE_DIR}"
)

target_link_libraries(unit_tests PRIVATE
    printguard_common
    printguard_domain
    printguard_pdf
    printguard_analysis
    printguard_fix
    printguard_orchestration
    Catch2::Catch2WithMain
)

add_test(NAME smoke_tests COMMAND unit_tests)

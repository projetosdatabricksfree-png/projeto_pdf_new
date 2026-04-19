enable_testing()

add_executable(unit_tests
    unit/smoke_test.cpp
    unit/domain_test.cpp
    unit/preset_schema_test.cpp
    unit/pdf_test.cpp
)

target_link_libraries(unit_tests PRIVATE
    printguard_common
    printguard_domain
    printguard_pdf
    Catch2::Catch2WithMain
)

add_test(NAME smoke_tests COMMAND unit_tests)

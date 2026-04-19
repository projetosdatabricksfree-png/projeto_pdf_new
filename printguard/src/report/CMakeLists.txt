add_library(printguard_report STATIC
    report_builder.cpp
)

target_include_directories(printguard_report PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(printguard_report PUBLIC
    printguard_common
    printguard_domain
    nlohmann_json::nlohmann_json
)

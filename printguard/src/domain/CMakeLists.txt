add_library(printguard_domain STATIC
    config_loader.cpp
    finding.cpp
    state_machine.cpp
)

target_include_directories(printguard_domain PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(printguard_domain PUBLIC
    printguard_common
    nlohmann_json::nlohmann_json
)

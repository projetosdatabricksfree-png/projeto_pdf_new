add_executable(printguard-api main.cpp)

target_link_libraries(printguard-api PRIVATE
    printguard_common
    printguard_orchestration
    httplib::httplib
    nlohmann_json::nlohmann_json
)

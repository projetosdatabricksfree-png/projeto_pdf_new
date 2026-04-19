add_executable(printguard-cli main.cpp)

target_link_libraries(printguard-cli PRIVATE
    printguard_common
    printguard_domain
    printguard_orchestration
    printguard_report
)

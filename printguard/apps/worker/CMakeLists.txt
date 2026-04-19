add_executable(printguard-worker main.cpp)

target_link_libraries(printguard-worker PRIVATE
    printguard_common
    printguard_persistence
    printguard_orchestration
    printguard_storage
    printguard_domain
    pqxx
)

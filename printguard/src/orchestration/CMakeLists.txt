add_library(printguard_orchestration STATIC
    orchestrator.cpp
    local_batch_processor.cpp
)

target_include_directories(printguard_orchestration PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(printguard_orchestration PUBLIC
    printguard_common
    printguard_analysis
    printguard_fix
    printguard_render
    printguard_report
    printguard_domain
    printguard_persistence
    printguard_pdf
    printguard_storage
)

add_library(printguard_persistence STATIC
    database.cpp
    job_repository.cpp
)

target_include_directories(printguard_persistence PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(printguard_persistence PUBLIC
    printguard_common
    pqxx
)

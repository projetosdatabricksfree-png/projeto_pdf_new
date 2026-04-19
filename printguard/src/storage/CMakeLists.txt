add_library(printguard_storage STATIC
    local_storage.cpp
)

target_include_directories(printguard_storage PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(printguard_storage PUBLIC
    printguard_common
)

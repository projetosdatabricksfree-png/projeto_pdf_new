add_library(printguard_render STATIC
    preview_renderer.cpp
)

target_include_directories(printguard_render PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(printguard_render PUBLIC
    printguard_common
)

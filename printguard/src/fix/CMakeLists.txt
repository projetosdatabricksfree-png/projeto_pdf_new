add_library(printguard_fix STATIC
    fix_engine.cpp
    fixes/normalize_boxes_fix.cpp
    fixes/convert_rgb_to_cmyk_fix.cpp
)

target_include_directories(printguard_fix PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(printguard_fix PUBLIC
    printguard_common
    printguard_domain
    qpdf::libqpdf
)

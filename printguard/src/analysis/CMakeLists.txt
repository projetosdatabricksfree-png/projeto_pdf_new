add_library(printguard_analysis STATIC
    rule_engine.cpp
    rules/page_geometry_rule.cpp
    rules/bleed_rule.cpp
    rules/color_space_rule.cpp
    rules/image_resolution_rule.cpp
    rules/safety_margin_rule.cpp
    rules/transparency_rule.cpp
)

target_include_directories(printguard_analysis PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(printguard_analysis PUBLIC
    printguard_common
    printguard_domain
    printguard_pdf
    qpdf::libqpdf
)

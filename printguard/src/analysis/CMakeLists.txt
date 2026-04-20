add_library(printguard_analysis STATIC
    rule_engine.cpp
    rules/page_geometry_rule.cpp
    rules/bleed_rule.cpp
    rules/color_space_rule.cpp
    rules/image_resolution_rule.cpp
    rules/safety_margin_rule.cpp
    rules/transparency_rule.cpp
    rules/tac_rule.cpp
    rules/output_intent_rule.cpp
    rules/white_overprint_rule.cpp
    rules/black_consistency_rule.cpp
    rules/annotation_rule.cpp
    rules/layer_rule.cpp
    rules/spot_color_rule.cpp
    rules/rotation_rule.cpp
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

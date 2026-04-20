add_library(printguard_fix STATIC
    color_transform_lcms.cpp
    pdf_color_utils.cpp
    fix_engine.cpp
    fixes/normalize_boxes_fix.cpp
    fixes/convert_rgb_to_cmyk_fix.cpp
    fixes/image_color_convert_fix.cpp
    fixes/attach_output_intent_fix.cpp
    fixes/tac_reduction_fix.cpp
    fixes/black_normalization_fix.cpp
    fixes/remove_white_overprint_fix.cpp
    fixes/remove_annotations_fix.cpp
    fixes/flatten_layers_fix.cpp
    fixes/spot_color_conversion_fix.cpp
    fixes/rotation_fix.cpp
)

target_include_directories(printguard_fix PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(printguard_fix PUBLIC
    printguard_common
    printguard_domain
    qpdf::libqpdf
    ${LCMS2_LIBRARIES}
)

target_include_directories(printguard_fix PRIVATE
    ${LCMS2_INCLUDE_DIRS}
)

target_compile_definitions(printguard_fix PRIVATE
    PRINTGUARD_PROJECT_SOURCE_DIR="${CMAKE_SOURCE_DIR}"
)

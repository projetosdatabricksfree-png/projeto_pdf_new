add_library(printguard_pdf STATIC
    pdf_loader.cpp
)

target_include_directories(printguard_pdf PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(printguard_pdf PUBLIC
    printguard_common
    qpdf::libqpdf
)

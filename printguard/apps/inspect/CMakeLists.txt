add_executable(printguard-inspect
    main.cpp
)

target_link_libraries(printguard-inspect PRIVATE
    printguard_common
    printguard_pdf
)

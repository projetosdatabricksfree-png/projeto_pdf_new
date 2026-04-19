add_library(printguard_common STATIC
    logging/logger.cpp
    crypto.cpp
)

target_include_directories(printguard_common PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(printguard_common PUBLIC
    spdlog::spdlog
    OpenSSL::SSL
    OpenSSL::Crypto
)

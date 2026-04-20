cmake_minimum_required(VERSION 3.22)
project(PrintGuard VERSION 0.1.0 LANGUAGES CXX)
enable_testing()

# Hard C++20 requirement
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
add_compile_definitions(POINTERHOLDER_TRANSITION=4)

# Security and hygiene flags
if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Werror -Wpedantic)
    add_compile_options(-fstack-protector-strong -D_GLIBCXX_ASSERTIONS)
    
    option(PRINTGUARD_COVERAGE "Enable code coverage reporting" OFF)
    if(PRINTGUARD_COVERAGE)
        add_compile_options(--coverage)
        add_link_options(--coverage)
    endif()
endif()

# Dependency Management (FetchContent)
include(FetchContent)
find_package(PkgConfig REQUIRED)

# 1. spdlog (Logging)
set(SPDLOG_BUILD_EXAMPLE OFF CACHE BOOL "" FORCE)
set(SPDLOG_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(SPDLOG_BUILD_TESTS_HO OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG v1.12.0
)
FetchContent_MakeAvailable(spdlog)
if(NOT MSVC)
    # Our project uses -Werror, but we don't want third-party deps to fail the build on
    # compiler-specific warnings.
    if(TARGET spdlog)
        target_compile_options(spdlog PRIVATE -Wno-error -Wno-error=array-bounds -Wno-array-bounds)
    endif()
endif()

# 2. nlohmann_json (JSON) - Using system package
find_package(nlohmann_json REQUIRED)

# 3. cpp-httplib (API)
set(HTTPLIB_INSTALL OFF CACHE BOOL "" FORCE)
set(HTTPLIB_TEST OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    httplib
    GIT_REPOSITORY https://github.com/yhirose/cpp-httplib.git
    GIT_TAG v0.14.1
)
FetchContent_MakeAvailable(httplib)

# 4. Catch2 (Testing)
set(CATCH_BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(CATCH_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(CATCH_BUILD_EXTRA_TESTS OFF CACHE BOOL "" FORCE)
set(CATCH_INSTALL_DOCS OFF CACHE BOOL "" FORCE)
set(CATCH_INSTALL_EXTRAS OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.4.0
)
FetchContent_MakeAvailable(Catch2)

# 5. libpqxx (PostgreSQL C++ Driver) - Requires libpq on system
set(SKIP_BUILD_TEST ON CACHE BOOL "" FORCE)
FetchContent_Declare(
    libpqxx
    GIT_REPOSITORY https://github.com/jtv/libpqxx.git
    GIT_TAG 7.7.5
)
FetchContent_MakeAvailable(libpqxx)

# 6. zlib (Required by QPDF) - Using system package
find_package(ZLIB REQUIRED)

# 7. JPEG (Required by QPDF) - Using system package
find_package(JPEG REQUIRED)

# 8. QPDF (PDF Engine) - Using system package
find_package(qpdf REQUIRED)

# 9. OpenSSL (For SHA256 and Security)
find_package(OpenSSL REQUIRED)

# 10. LittleCMS2 (Color conversion)
pkg_check_modules(LCMS2 REQUIRED lcms2)

# Include directories
add_library(PrintGuard_Config INTERFACE)
target_include_directories(PrintGuard_Config INTERFACE include)
# Using include_directories for now as in Sprint 01 or fix per module

# Targets
add_subdirectory(src/common)
add_subdirectory(src/persistence)
add_subdirectory(src/storage)
add_subdirectory(src/domain)
add_subdirectory(src/orchestration)
add_subdirectory(src/pdf)
add_subdirectory(src/analysis)
add_subdirectory(src/fix)
add_subdirectory(src/render)
add_subdirectory(src/report)
add_subdirectory(apps/api)
add_subdirectory(apps/worker)
add_subdirectory(apps/inspect)
add_subdirectory(apps/cli)
add_subdirectory(tests)

# Summary
message(STATUS "--------------------------------------------------")
message(STATUS "PrintGuard Build Configuration:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  Standard: C++20")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  OpenSSL: ${OPENSSL_VERSION}")
message(STATUS "--------------------------------------------------")

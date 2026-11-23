cmake_minimum_required(VERSION 3.20)
project(DuckOSWindowsCompat VERSION 0.1.0 LANGUAGES CXX)

option(DUCKOS_COMPAT_BUILD_TESTS "Build compatibility subsystem tests" ON)

add_library(duckos_compat
    src/pe_image.cpp
    src/prefix_manager.cpp
    src/runner.cpp
)
target_include_directories(duckos_compat PUBLIC include)
target_compile_features(duckos_compat PUBLIC cxx_std_20)

if(MSVC)
    target_compile_options(duckos_compat PRIVATE /W4 /permissive-)
else()
    target_compile_options(duckos_compat PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
endif()

add_executable(os-run src/main.cpp)
target_link_libraries(os-run PRIVATE duckos_compat)

if(DUCKOS_COMPAT_BUILD_TESTS)
    enable_testing()
    add_executable(duckos_pe_tests tests/pe_image_tests.cpp)
    target_link_libraries(duckos_pe_tests PRIVATE duckos_compat)
    add_test(NAME pe-image-inspection COMMAND duckos_pe_tests)

    add_executable(duckos_prefix_tests tests/prefix_tests.cpp)
    target_link_libraries(duckos_prefix_tests PRIVATE duckos_compat)
    add_test(NAME prefix-manager COMMAND duckos_prefix_tests)
endif()

install(TARGETS os-run RUNTIME DESTINATION bin)

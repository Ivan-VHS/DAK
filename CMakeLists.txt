cmake_minimum_required(VERSION 3.16)
project(DuckOSFoundation LANGUAGES C)

set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

option(DUCKOS_BUILD_DABI64_TESTS "Build the Reaper host adapter contract tests" OFF)
set(REAPER_SOURCE_DIR "" CACHE PATH "Path to a Reaper checkout containing src/dabi64.c and include/reaper/dabi64.h")

if(DUCKOS_BUILD_DABI64_TESTS)
    if(NOT EXISTS "${REAPER_SOURCE_DIR}/src/dabi64.c" OR
       NOT EXISTS "${REAPER_SOURCE_DIR}/include/reaper/dabi64.h")
        message(FATAL_ERROR "Set REAPER_SOURCE_DIR to a Reaper checkout with the DABI64 v1 runtime")
    endif()

    add_executable(duckos-reaper-host-tests
        tests/test_reaper_host.c
        ${REAPER_SOURCE_DIR}/src/dabi64.c
    )
    target_include_directories(duckos-reaper-host-tests PRIVATE
        include
        ${REAPER_SOURCE_DIR}/include
    )
    if(MSVC)
        target_compile_options(duckos-reaper-host-tests PRIVATE /W4)
    else()
        target_compile_options(duckos-reaper-host-tests PRIVATE
            -Wall -Wextra -Wpedantic -Wconversion -Wshadow
        )
    endif()

    enable_testing()
    add_test(NAME duckos-reaper-host-adapter COMMAND duckos-reaper-host-tests)
endif()

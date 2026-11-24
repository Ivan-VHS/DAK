cmake_minimum_required(VERSION 3.21)
project(DuckOSFoundation VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

option(DUCKOS_ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
option(DUCKOS_ENABLE_REAPER_CONTRACT_TESTS "Enable Reaper/DuckOS boot-contract parity tests when the submodule is available" ON)
set(DUCKOS_REAPER_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/projects/reaper" CACHE PATH "Path to the Reaper source checkout")

add_library(duckos_boot_contract STATIC
    foundation/boot_info.c
    foundation/boot_info.h
)
target_include_directories(duckos_boot_contract PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/foundation
)

if(MSVC)
    target_compile_options(duckos_boot_contract PRIVATE /W4 /sdl)
else()
    target_compile_options(duckos_boot_contract PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(DUCKOS_ENABLE_SANITIZERS)
    if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(duckos_boot_contract PUBLIC -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(duckos_boot_contract PUBLIC -fsanitize=address,undefined)
    else()
        message(FATAL_ERROR "DUCKOS_ENABLE_SANITIZERS requires GCC or Clang")
    endif()
endif()

include(CTest)
if(BUILD_TESTING)
    add_executable(duckos_boot_info_tests tests/test_boot_info.c)
    target_link_libraries(duckos_boot_info_tests PRIVATE duckos_boot_contract)
    if(MSVC)
        target_compile_options(duckos_boot_info_tests PRIVATE /W4 /sdl)
    else()
        target_compile_options(duckos_boot_info_tests PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME duckos-boot-info-contract COMMAND duckos_boot_info_tests)

    add_executable(duckos_boot_info_conformance tests/test_boot_info_conformance.c)
    target_link_libraries(duckos_boot_info_conformance PRIVATE duckos_boot_contract)
    if(MSVC)
        target_compile_options(duckos_boot_info_conformance PRIVATE /W4 /sdl)
    else()
        target_compile_options(duckos_boot_info_conformance PRIVATE -Wall -Wextra -Wpedantic)
    endif()

    if(DUCKOS_ENABLE_REAPER_CONTRACT_TESTS)
        find_package(Python3 COMPONENTS Interpreter QUIET)
        if(Python3_Interpreter_FOUND AND EXISTS "${DUCKOS_REAPER_SOURCE_DIR}/reaper/__main__.py")
            add_test(
                NAME duckos-reaper-boot-contract-parity
                COMMAND ${Python3_EXECUTABLE}
                    "${CMAKE_CURRENT_SOURCE_DIR}/tools/check_reaper_boot_contract.py"
                    --reaper-root "${DUCKOS_REAPER_SOURCE_DIR}"
                    --c-harness "$<TARGET_FILE:duckos_boot_info_conformance>"
            )
            set_tests_properties(duckos-reaper-boot-contract-parity PROPERTIES TIMEOUT 240)
        else()
            message(STATUS "Reaper boot-contract parity disabled: initialize projects/reaper or set DUCKOS_REAPER_SOURCE_DIR")
        endif()
    endif()
endif()

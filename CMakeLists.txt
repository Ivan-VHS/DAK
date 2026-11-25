cmake_minimum_required(VERSION 3.21)
project(DuckOSFoundation VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

option(DUCKOS_ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)

add_library(duckos_boot_contract STATIC
    foundation/boot_info.c
    foundation/boot_info.h
    foundation/frame_allocator.c
    foundation/frame_allocator.h
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

    add_executable(duckos_frame_allocator_tests tests/test_frame_allocator.c)
    target_link_libraries(duckos_frame_allocator_tests PRIVATE duckos_boot_contract)
    if(MSVC)
        target_compile_options(duckos_frame_allocator_tests PRIVATE /W4 /sdl)
    else()
        target_compile_options(duckos_frame_allocator_tests PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME duckos-frame-allocator COMMAND duckos_frame_allocator_tests)
endif()

if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|amd64)$")
    add_custom_target(duckos-boot-iso
        COMMAND bash "${CMAKE_CURRENT_SOURCE_DIR}/boot/build-iso.sh"
            --work-dir "${CMAKE_BINARY_DIR}/duckos-boot"
            --output "${CMAKE_BINARY_DIR}/DuckOS-Stage1-x86_64.iso"
        BYPRODUCTS
            "${CMAKE_BINARY_DIR}/DuckOS-Stage1-x86_64.iso"
            "${CMAKE_BINARY_DIR}/DuckOS-Stage1-x86_64.iso.sha256"
        WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
        USES_TERMINAL
        COMMENT "Building the DuckOS x86_64 BIOS/UEFI stage-1 ISO"
    )
endif()

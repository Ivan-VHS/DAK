cmake_minimum_required(VERSION 3.21)
project(DuckOSFoundation VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

option(DUCKOS_ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)

add_library(duckos_boot_contract STATIC
    foundation/boot_info.c
    foundation/boot_info.h
)
target_include_directories(duckos_boot_contract PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/foundation
)

add_library(duckos_security_foundation STATIC
    foundation/security.c
    foundation/security.h
)
target_include_directories(duckos_security_foundation PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/foundation
)
if(MSVC)
    target_compile_options(duckos_security_foundation PRIVATE /W4 /sdl)
else()
    target_compile_options(duckos_security_foundation PRIVATE -Wall -Wextra -Wpedantic)
endif()

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

    add_executable(duckos_security_tests tests/test_security_foundation.c)
    target_link_libraries(duckos_security_tests PRIVATE duckos_security_foundation)
    if(MSVC)
        target_compile_options(duckos_security_tests PRIVATE /W4 /sdl)
    else()
        target_compile_options(duckos_security_tests PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME duckos-security-foundation-contract COMMAND duckos_security_tests)
endif()

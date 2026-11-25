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
    foundation/idt.c
    foundation/idt.h
)
target_include_directories(duckos_boot_contract PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/foundation
)

add_library(duckos_desktop_ipc STATIC
    foundation/desktop_ipc.c
    foundation/desktop_ipc.h
    projects/reaper/src/system.c
    projects/reaper/src/dabi64_desktop.c
)
target_include_directories(duckos_desktop_ipc PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/foundation
    ${CMAKE_CURRENT_SOURCE_DIR}/projects/reaper/include
)
set_target_properties(duckos_desktop_ipc PROPERTIES
    C_STANDARD 17
    C_STANDARD_REQUIRED ON
    C_EXTENSIONS OFF
)
if(MSVC)
    target_compile_options(duckos_desktop_ipc PRIVATE /W4 /sdl)
else()
    target_compile_options(duckos_desktop_ipc PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
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
        target_compile_options(duckos_desktop_ipc PUBLIC -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(duckos_desktop_ipc PUBLIC -fsanitize=address,undefined)
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

    add_executable(duckos_idt_tests tests/test_idt.c)
    target_link_libraries(duckos_idt_tests PRIVATE duckos_boot_contract)
    target_include_directories(duckos_idt_tests PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/kernel/arch/x86_64
    )
    if(MSVC)
        target_compile_options(duckos_idt_tests PRIVATE /W4 /sdl)
    else()
        target_compile_options(duckos_idt_tests PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME duckos-idt-contract COMMAND duckos_idt_tests)

    add_executable(duckos_desktop_ipc_tests tests/test_desktop_ipc.c)
    target_link_libraries(duckos_desktop_ipc_tests PRIVATE duckos_desktop_ipc)
    if(MSVC)
        target_compile_options(duckos_desktop_ipc_tests PRIVATE /W4 /sdl)
    else()
        target_compile_options(duckos_desktop_ipc_tests PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
    endif()
    add_test(NAME duckos-dabi64-ipc-foundation COMMAND duckos_desktop_ipc_tests)
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


if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|amd64)$")
    add_custom_target(duckos-release-iso
        COMMAND bash "${CMAKE_CURRENT_SOURCE_DIR}/boot/build-release-iso.sh"
            --work-dir "${CMAKE_BINARY_DIR}/release"
            --output "${CMAKE_BINARY_DIR}/DuckOS-Release-x86_64.iso"
        BYPRODUCTS
            "${CMAKE_BINARY_DIR}/DuckOS-Release-x86_64.iso"
            "${CMAKE_BINARY_DIR}/DuckOS-Release-x86_64.iso.sha256"
        WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
        USES_TERMINAL
        COMMENT "Building the DuckOS ecosystem release ISO and testing federated projects"
    )
endif()

option(DUCKOS_BUILD_NATIVE_MORA "Build the host-native Mora desktop shell when Qt 6 Widgets is available" ON)
if(DUCKOS_BUILD_NATIVE_MORA)
    include(CheckLanguage)
    check_language(CXX)
    if(CMAKE_CXX_COMPILER)
        enable_language(CXX)
        set(CMAKE_CXX_STANDARD 17)
        set(CMAKE_CXX_STANDARD_REQUIRED ON)
        set(CMAKE_CXX_EXTENSIONS OFF)

        find_package(Qt6 6.4 COMPONENTS Widgets QUIET)
        if(Qt6_FOUND)
            add_executable(duckos_mora_native
                mora/native/main.cpp
            )
            target_link_libraries(duckos_mora_native PRIVATE Qt6::Widgets)
            target_compile_definitions(duckos_mora_native PRIVATE
                DUCKOS_MORA_CATALOG_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/mora/apps.json\"
                DUCKOS_MORA_THEME_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/mora/theme.json\"
            )
            if(MSVC)
                target_compile_options(duckos_mora_native PRIVATE /W4 /permissive-)
            else()
                target_compile_options(duckos_mora_native PRIVATE -Wall -Wextra -Wpedantic)
            endif()

            if(BUILD_TESTING)
                add_test(
                    NAME duckos-mora-native-smoke
                    COMMAND duckos_mora_native --self-test
                )
                set_tests_properties(duckos-mora-native-smoke PROPERTIES
                    ENVIRONMENT "QT_QPA_PLATFORM=offscreen"
                )
            endif()
        else()
            message(STATUS "Qt 6 Widgets was not found; the optional native Mora target is skipped.")
        endif()
    else()
        message(STATUS "No C++ compiler was found; the optional native Mora target is skipped.")
    endif()
endif()

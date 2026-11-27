cmake_minimum_required(VERSION 3.21)
project(DAKFoundation VERSION 0.1.0 LANGUAGES C)

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
    foundation/gdt_descriptor.c
    foundation/gdt_descriptor.h
)
add_library(duckos_processor_runtime STATIC
    kernel/processor/scheduler.c
    kernel/arch/x86_64/context.c
    kernel/arch/x86_64/cpu.c
)
target_include_directories(duckos_processor_runtime PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/kernel/processor
    ${CMAKE_CURRENT_SOURCE_DIR}/kernel/arch/x86_64
)
if(MSVC)
    target_compile_options(duckos_processor_runtime PRIVATE /W4 /sdl /experimental:c11atomics)
else()
    target_compile_options(duckos_processor_runtime PRIVATE -Wall -Wextra -Wpedantic)
endif()

set(DUCKOS_HAS_X86_64_CONTEXT OFF)
if(UNIX AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|amd64)$")
    enable_language(ASM)
    target_sources(duckos_processor_runtime PRIVATE kernel/arch/x86_64/context.S)
    set(DUCKOS_HAS_X86_64_CONTEXT ON)
endif()

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

    add_executable(duckos_gdt_tests tests/test_gdt.c)
    target_link_libraries(duckos_gdt_tests PRIVATE duckos_boot_contract)
    if(MSVC)
        target_compile_options(duckos_gdt_tests PRIVATE /W4 /sdl)
    else()
        target_compile_options(duckos_gdt_tests PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME duckos-x86-64-gdt-tss COMMAND duckos_gdt_tests)

    add_executable(duckos_processor_scheduler_tests tests/test_processor_scheduler.c)
    target_link_libraries(duckos_processor_scheduler_tests PRIVATE duckos_processor_runtime)
    add_test(NAME duckos-processor-scheduler COMMAND duckos_processor_scheduler_tests)

    if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|amd64)$")
        add_executable(duckos_x86_64_cpu_tests tests/test_x86_64_cpu.c)
        target_link_libraries(duckos_x86_64_cpu_tests PRIVATE duckos_processor_runtime)
        add_test(NAME duckos-x86-64-cpu-probe COMMAND duckos_x86_64_cpu_tests)
    endif()

    if(DUCKOS_HAS_X86_64_CONTEXT)
        add_executable(duckos_x86_64_context_tests tests/test_x86_64_context.c)
        target_link_libraries(duckos_x86_64_context_tests PRIVATE duckos_processor_runtime)
        add_test(NAME duckos-x86-64-context-switch COMMAND duckos_x86_64_context_tests)
    endif()
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

option(DAK_BUILD_NATIVE_DESKTOP "Build the DAK host-native desktop shell when Qt 6 Widgets is available" ON)
if(DAK_BUILD_NATIVE_DESKTOP)
    include(CheckLanguage)
    check_language(CXX)
    if(CMAKE_CXX_COMPILER)
        enable_language(CXX)
        set(CMAKE_CXX_STANDARD 17)
        set(CMAKE_CXX_STANDARD_REQUIRED ON)
        set(CMAKE_CXX_EXTENSIONS OFF)

        find_package(Qt6 6.4 COMPONENTS Widgets QUIET)
        if(Qt6_FOUND)
            add_executable(dak_desktop_native
                mora/native/main.cpp
            )
            target_link_libraries(dak_desktop_native PRIVATE Qt6::Widgets)
            target_compile_definitions(dak_desktop_native PRIVATE
                DAK_DESKTOP_CATALOG_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/mora/apps.json\"
                DAK_DESKTOP_THEME_PATH=\"${CMAKE_CURRENT_SOURCE_DIR}/mora/theme.json\"
            )
            if(MSVC)
                target_compile_options(dak_desktop_native PRIVATE /W4 /permissive-)
            else()
                target_compile_options(dak_desktop_native PRIVATE -Wall -Wextra -Wpedantic)
            endif()

            if(BUILD_TESTING)
                add_test(
                    NAME dak-native-desktop-smoke
                    COMMAND dak_desktop_native --self-test
                )
                set_tests_properties(dak-native-desktop-smoke PROPERTIES
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

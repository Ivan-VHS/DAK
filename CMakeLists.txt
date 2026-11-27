cmake_minimum_required(VERSION 3.21)
project(DAKFoundation VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

option(DAKOS_ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)

add_library(dakos_boot_contract STATIC
    foundation/boot_info.c
    foundation/boot_info.h
    foundation/frame_allocator.c
    foundation/frame_allocator.h
    foundation/idt.c
    foundation/idt.h
    foundation/gdt_descriptor.c
    foundation/gdt_descriptor.h
)
target_include_directories(dakos_boot_contract PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/foundation
)

if(MSVC)
    target_compile_options(dakos_boot_contract PRIVATE /W4 /sdl)
else()
    target_compile_options(dakos_boot_contract PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(DAKOS_ENABLE_SANITIZERS)
    if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(dakos_boot_contract PUBLIC -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(dakos_boot_contract PUBLIC -fsanitize=address,undefined)
    else()
        message(FATAL_ERROR "DAKOS_ENABLE_SANITIZERS requires GCC or Clang")
    endif()
endif()

include(CTest)
if(BUILD_TESTING)
    add_executable(dakos_boot_info_tests tests/test_boot_info.c)
    target_link_libraries(dakos_boot_info_tests PRIVATE dakos_boot_contract)
    if(MSVC)
        target_compile_options(dakos_boot_info_tests PRIVATE /W4 /sdl)
    else()
        target_compile_options(dakos_boot_info_tests PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME dakos-boot-info-contract COMMAND dakos_boot_info_tests)

    add_executable(dakos_frame_allocator_tests tests/test_frame_allocator.c)
    target_link_libraries(dakos_frame_allocator_tests PRIVATE dakos_boot_contract)
    if(MSVC)
        target_compile_options(dakos_frame_allocator_tests PRIVATE /W4 /sdl)
    else()
        target_compile_options(dakos_frame_allocator_tests PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME dakos-frame-allocator COMMAND dakos_frame_allocator_tests)

    add_executable(dakos_idt_tests tests/test_idt.c)
    target_link_libraries(dakos_idt_tests PRIVATE dakos_boot_contract)
    target_include_directories(dakos_idt_tests PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/kernel/arch/x86_64
    )
    if(MSVC)
        target_compile_options(dakos_idt_tests PRIVATE /W4 /sdl)
    else()
        target_compile_options(dakos_idt_tests PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME dakos-idt-contract COMMAND dakos_idt_tests)

    add_executable(dakos_gdt_tests tests/test_gdt.c)
    target_link_libraries(dakos_gdt_tests PRIVATE dakos_boot_contract)
    if(MSVC)
        target_compile_options(dakos_gdt_tests PRIVATE /W4 /sdl)
    else()
        target_compile_options(dakos_gdt_tests PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME dakos-x86-64-gdt-tss COMMAND dakos_gdt_tests)
endif()

if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|amd64)$")
    add_custom_target(dakos-boot-iso
        COMMAND bash "${CMAKE_CURRENT_SOURCE_DIR}/boot/build-iso.sh"
            --work-dir "${CMAKE_BINARY_DIR}/dakos-boot"
            --output "${CMAKE_BINARY_DIR}/DAKOS-Stage1-x86_64.iso"
        BYPRODUCTS
            "${CMAKE_BINARY_DIR}/DAKOS-Stage1-x86_64.iso"
            "${CMAKE_BINARY_DIR}/DAKOS-Stage1-x86_64.iso.sha256"
        WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
        USES_TERMINAL
        COMMENT "Building the DAKOS x86_64 BIOS/UEFI stage-1 ISO"
    )
endif()


if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|amd64)$")
    add_custom_target(dakos-release-iso
        COMMAND bash "${CMAKE_CURRENT_SOURCE_DIR}/boot/build-release-iso.sh"
            --work-dir "${CMAKE_BINARY_DIR}/release"
            --output "${CMAKE_BINARY_DIR}/DAKOS-Release-x86_64.iso"
        BYPRODUCTS
            "${CMAKE_BINARY_DIR}/DAKOS-Release-x86_64.iso"
            "${CMAKE_BINARY_DIR}/DAKOS-Release-x86_64.iso.sha256"
        WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
        USES_TERMINAL
        COMMENT "Building the DAKOS ecosystem release ISO and testing federated projects"
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

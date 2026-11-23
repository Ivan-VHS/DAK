cmake_minimum_required(VERSION 3.16)
project(DuckOSFoundation LANGUAGES C)

set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

option(DUCKOS_BUILD_KERNEL "Build the freestanding x86-64 Multiboot2 kernel" OFF)
option(DUCKOS_BUILD_DABI64_TESTS "Build the Reaper host adapter contract tests" OFF)
set(REAPER_SOURCE_DIR "" CACHE PATH "Path to a Reaper checkout containing src/dabi64.c and include/reaper/dabi64.h")

if(DUCKOS_BUILD_KERNEL)
    if(NOT CMAKE_C_COMPILER_ID MATCHES "GNU|Clang" OR
       NOT CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64|amd64")
        message(FATAL_ERROR "DuckOS kernel target currently requires an x86-64 GCC or Clang toolchain")
    endif()

    enable_language(ASM)
    set(DUCKOS_KERNEL_SOURCES
        boot/entry.S
        kernel/arch/x86_64/context_switch.S
        kernel/arch/x86_64/interrupts.S
        kernel/arch/x86_64/interrupts.c
        kernel/src/audio.c
        kernel/src/heap.c
        kernel/src/interrupts.c
        kernel/src/kernel.c
        kernel/src/memory.c
        kernel/src/process.c
        kernel/src/serial.c
        kernel/src/string.c
        kernel/src/syscall.c
        kernel/src/vfs.c
    )
    add_executable(duckos-kernel.elf $DUCKOS_KERNEL_SOURCES)
    target_include_directories(duckos-kernel.elf PRIVATE
        kernel/include
        include
    )
    target_compile_options(duckos-kernel.elf PRIVATE
        $<$<COMPILE_LANGUAGE:C>:-std=c17>
        $<$<COMPILE_LANGUAGE:C>:-ffreestanding>
        $<$<COMPILE_LANGUAGE:C>:-fno-builtin>
        $<$<COMPILE_LANGUAGE:C>:-fno-stack-protector>
        $<$<COMPILE_LANGUAGE:C>:-fno-pic>
        $<$<COMPILE_LANGUAGE:C>:-fno-pie>
        $<$<COMPILE_LANGUAGE:C>:-fno-asynchronous-unwind-tables>
        $<$<COMPILE_LANGUAGE:C>:-fno-unwind-tables>
        $<$<COMPILE_LANGUAGE:C>:-m64>
        $<$<COMPILE_LANGUAGE:C>:-mno-red-zone>
        $<$<COMPILE_LANGUAGE:C>:-mno-mmx>
        $<$<COMPILE_LANGUAGE:C>:-mno-sse>
        $<$<COMPILE_LANGUAGE:C>:-mno-sse2>
        $<$<COMPILE_LANGUAGE:C>:-Wall>
        $<$<COMPILE_LANGUAGE:C>:-Wextra>
        $<$<COMPILE_LANGUAGE:C>:-Wpedantic>
        $<$<COMPILE_LANGUAGE:C>:-Wconversion>
        $<$<COMPILE_LANGUAGE:C>:-Wshadow>
        $<$<COMPILE_LANGUAGE:ASM>:-m64>
    )
    target_link_options(duckos-kernel.elf PRIVATE
        -m64
        -nostdlib
        -static
        -no-pie
        -Wl,--build-id=none
        -Wl,-z,max-page-size=0x1000
        -Wl,-T,$CMAKE_CURRENT_SOURCE_DIR/kernel/linker.ld
    )
    set_target_properties(duckos-kernel.elf PROPERTIES
        LINKER_LANGUAGE C
        OUTPUT_NAME duckos-kernel
        SUFFIX .elf
    )

    find_program(DUCKOS_GRUB_FILE grub-file)
    if(DUCKOS_GRUB_FILE)
        add_custom_target(duckos-check-multiboot
            COMMAND $DUCKOS_GRUB_FILE --is-x86-multiboot2 $<TARGET_FILE:duckos-kernel.elf>
            DEPENDS duckos-kernel.elf
            VERBATIM
        )
    endif()

    find_program(DUCKOS_GRUB_MKRESCUE grub-mkrescue)
    if(DUCKOS_GRUB_MKRESCUE)
        set(DUCKOS_ISO_ROOT $CMAKE_CURRENT_BINARY_DIR/duckos-iso-root)
        set(DUCKOS_ISO_FILE $CMAKE_CURRENT_BINARY_DIR/duckos.iso)
        add_custom_command(
            OUTPUT $DUCKOS_ISO_FILE
            COMMAND $CMAKE_COMMAND -E make_directory
                $DUCKOS_ISO_ROOT/boot/grub
            COMMAND $CMAKE_COMMAND -E copy
                $<TARGET_FILE:duckos-kernel.elf>
                $DUCKOS_ISO_ROOT/boot/duckos-kernel.elf
            COMMAND $CMAKE_COMMAND -E copy
                $CMAKE_CURRENT_SOURCE_DIR/boot/grub.cfg
                $DUCKOS_ISO_ROOT/boot/grub/grub.cfg
            COMMAND $DUCKOS_GRUB_MKRESCUE -o $DUCKOS_ISO_FILE $DUCKOS_ISO_ROOT
            DEPENDS duckos-kernel.elf boot/grub.cfg
            VERBATIM
        )
        add_custom_target(duckos-iso DEPENDS $DUCKOS_ISO_FILE)
    endif()
endif()

if(DUCKOS_BUILD_DABI64_TESTS)
    if(NOT EXISTS "$REAPER_SOURCE_DIR/src/dabi64.c" OR
       NOT EXISTS "$REAPER_SOURCE_DIR/include/reaper/dabi64.h")
        message(FATAL_ERROR "Set REAPER_SOURCE_DIR to a Reaper checkout with the DABI64 v1 runtime")
    endif()

    add_executable(duckos-reaper-host-tests
        tests/test_reaper_host.c
        $REAPER_SOURCE_DIR/src/dabi64.c
    )
    target_include_directories(duckos-reaper-host-tests PRIVATE
        include
        $REAPER_SOURCE_DIR/include
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

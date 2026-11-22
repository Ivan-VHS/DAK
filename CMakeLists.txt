cmake_minimum_required(VERSION 3.16)
project(DuckOS_ABI VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

add_library(duckos_abi STATIC src/abi.c
    runtime/runtime.c)
target_include_directories(duckos_abi PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

if(MSVC)
    target_compile_options(duckos_abi PRIVATE /W4)
else()
    target_compile_options(duckos_abi PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
endif()

enable_testing()
add_executable(duckos-abi-tests tests/abi_contract.c)
target_link_libraries(duckos-abi-tests PRIVATE duckos_abi)
add_executable(duckos-runtime-tests tests/runtime_contract.c)
target_link_libraries(duckos-runtime-tests PRIVATE duckos_abi)
add_test(NAME duckos-runtime COMMAND duckos-runtime-tests)

add_test(NAME duckos-abi-contract COMMAND duckos-abi-tests)

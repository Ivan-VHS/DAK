cmake_minimum_required(VERSION 3.16)
project(DuckOSDabi64 VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

add_library(duckos_dabi64 STATIC src/abi/dabi64.c)
target_include_directories(duckos_dabi64 PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

if(MSVC)
    target_compile_options(duckos_dabi64 PRIVATE /W4)
else()
    target_compile_options(duckos_dabi64 PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
endif()

include(CTest)
if(BUILD_TESTING)
    add_executable(duckos-dabi64-tests tests/abi_dabi64.c)
    target_link_libraries(duckos-dabi64-tests PRIVATE duckos_dabi64)
    add_test(NAME duckos-dabi64-abi COMMAND duckos-dabi64-tests)
endif()

cmake_minimum_required(VERSION 3.20)
project(DuckOSNativeDesktop VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

find_package(PkgConfig REQUIRED)
pkg_check_modules(X11_STACK REQUIRED IMPORTED_TARGET
    x11
    xcomposite
    xdamage
    xrender
    xfixes
    xext
)

add_executable(duckos-compositor native/mora-x11.c)
target_link_libraries(duckos-compositor PRIVATE PkgConfig::X11_STACK)
target_compile_definitions(duckos-compositor PRIVATE _POSIX_C_SOURCE=200809L)
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(duckos-compositor PRIVATE
        -Wall -Wextra -Wpedantic -Wformat=2 -Wshadow -Wconversion
    )
endif()

install(TARGETS duckos-compositor RUNTIME DESTINATION bin)

enable_testing()
add_test(NAME compositor-version COMMAND duckos-compositor --version)

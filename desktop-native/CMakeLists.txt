cmake_minimum_required(VERSION 3.21)
project(DuckOSNativeDesktop VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 6.4 REQUIRED COMPONENTS Core Widgets)

add_library(duckos-desktop-core STATIC
    src/application_catalog.cpp
    src/application_catalog.hpp
    src/application_launcher.cpp
    src/application_launcher.hpp
)
target_link_libraries(duckos-desktop-core PUBLIC Qt6::Core)
target_include_directories(duckos-desktop-core PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src")

if(MSVC)
    target_compile_options(duckos-desktop-core PRIVATE /W4 /permissive- /EHsc)
else()
    target_compile_options(duckos-desktop-core PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
endif()

add_executable(duckos-desktop WIN32
    src/main.cpp
    src/desktop_window.cpp
    src/desktop_window.hpp
    src/native_apps.cpp
    src/native_apps.hpp
)
target_link_libraries(duckos-desktop PRIVATE duckos-desktop-core Qt6::Widgets)
target_include_directories(duckos-desktop PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_compile_definitions(duckos-desktop PRIVATE
    DUCKOS_DESKTOP_VERSION="${PROJECT_VERSION}"
    DUCKOS_SOURCE_ROOT="${CMAKE_CURRENT_SOURCE_DIR}/.."
)

if(MSVC)
    target_compile_options(duckos-desktop PRIVATE /W4 /permissive- /EHsc)
else()
    target_compile_options(duckos-desktop PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
endif()

include(CTest)
if(BUILD_TESTING)
    add_executable(duckos-desktop-catalog-tests tests/test_application_catalog.cpp)
    target_link_libraries(duckos-desktop-catalog-tests PRIVATE duckos-desktop-core Qt6::Core)
    target_compile_definitions(duckos-desktop-catalog-tests PRIVATE
        DUCKOS_SOURCE_ROOT="${CMAKE_CURRENT_SOURCE_DIR}/.."
    )
    add_test(NAME native-desktop-catalog COMMAND duckos-desktop-catalog-tests)

    add_test(NAME native-desktop-smoke
        COMMAND duckos-desktop --smoke-test --root "${CMAKE_CURRENT_SOURCE_DIR}/..")
    set_tests_properties(native-desktop-smoke PROPERTIES
        ENVIRONMENT "QT_QPA_PLATFORM=offscreen"
        TIMEOUT 15
    )
endif()

install(TARGETS duckos-desktop RUNTIME DESTINATION release/bin)

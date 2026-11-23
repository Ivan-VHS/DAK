add_library(serein_core
    src/serein.cpp
)
target_include_directories(serein_core PUBLIC include)
target_compile_features(serein_core PUBLIC cxx_std_20)

if(MSVC)
    target_compile_options(serein_core PRIVATE /W4 /permissive- /sdl)
else()
    target_compile_options(serein_core PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
endif()

add_executable(serein src/main.cpp)
target_link_libraries(serein PRIVATE serein_core)

include(CTest)
if(BUILD_TESTING)
    add_executable(serein-tests ../tests/serein_tests.cpp)
    target_link_libraries(serein-tests PRIVATE serein_core)
    add_test(NAME serein-contract-tests COMMAND serein-tests)
endif()
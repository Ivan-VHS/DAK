cmake_minimum_required(VERSION 3.20)

project(DuckOS VERSION 0.2.0 LANGUAGES CXX)

include(CTest)

add_subdirectory(native)

install(TARGETS serein RUNTIME DESTINATION bin)
install(DIRECTORY mora/ DESTINATION share/duckos/mora)
install(FILES mora/manifest.json mora/apps.json mora/app-manifest.schema.json
        DESTINATION share/duckos/mora)
cmake_minimum_required(VERSION 3.20)
project(PaceTraceLauncher LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(launcher launcher.cpp)

target_link_libraries(launcher PRIVATE
    kernel32 user32 shell32 ole32 winhttp shlwapi)

target_link_options(launcher PRIVATE -static -O2 -s)

target_compile_options(launcher PRIVATE
    -finput-charset=UTF-8 -Wall -Wpedantic)

cmake_minimum_required(VERSION 3.22.1)
project("strategy_native_engine" C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_C_STANDARD 99)

# 1. Collect all raw Lua 5.4.6 ANSI C source files
file(GLOB LUA_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/lua/*.c
)

# 2. Reference Rust core static library for the current target ABI
set(RUST_LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../rust/target/libs/${ANDROID_ABI}")

add_library(rust_strategy_core STATIC IMPORTED)
set_target_properties(rust_strategy_core PROPERTIES
    IMPORTED_LOCATION "${RUST_LIB_DIR}/libstrategy_core.a"
)

# 3. Define main native strategy shared library
add_library(
    native-strategy-engine
    SHARED
    strategy_engine.cpp
    ${LUA_SOURCES}
)

target_include_directories(
    native-strategy-engine
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/lua
)

# 4. Link dependencies: Rust Core, Android Log, and Math library
find_library(log-lib log)

target_link_libraries(
    native-strategy-engine
    rust_strategy_core
    ${log-lib}
    m
)

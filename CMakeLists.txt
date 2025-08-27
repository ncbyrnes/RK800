cmake_minimum_required(VERSION 3.22.1)
project(RK800
        VERSION 1.0
        DESCRIPTION "RK800 Project"
        LANGUAGES C)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# set build type to release by default and add NDEBUG define for release builds
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

if(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_compile_definitions(NDEBUG)
endif()

if(ANDROID)
    if(ANDROID_ABI STREQUAL "arm64-v8a")
        set(TARGET_ARCH "android_aarch64")
    elseif(ANDROID_ABI STREQUAL "armeabi-v7a")
        set(TARGET_ARCH "android_arm32")
    else()
        set(TARGET_ARCH "android_${ANDROID_ABI}")
    endif()
else()
    set(TARGET_ARCH "linux_x86_64")
endif()

string(TOLOWER ${CMAKE_BUILD_TYPE} BUILD_TYPE_LOWER)
set(TARGET_SUFFIX "${TARGET_ARCH}_${BUILD_TYPE_LOWER}")

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/rk800/assets)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/rk800/assets)

option(BUILD_DAEMON "Build daemon project" ON)

if(BUILD_DAEMON)
    add_subdirectory(daemon/)
endif()
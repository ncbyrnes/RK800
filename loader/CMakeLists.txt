set(LOADER "loader-${TARGET_SUFFIX}")

set (LOADER_FLAGS -Wall -Werror -Wextra -Wpedantic -Wconversion -Wunreachable-code -Os)

add_executable(${LOADER})
target_compile_options(${LOADER} PUBLIC ${LOADER_FLAGS})
target_include_directories(${LOADER} PUBLIC ${CMAKE_SOURCE_DIR} ${CMAKE_SOURCE_DIR}/loader/include)
target_sources(${LOADER} PRIVATE ${CMAKE_SOURCE_DIR}/common.c)

add_subdirectory(src/)
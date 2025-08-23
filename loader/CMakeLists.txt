set(LOADER "loader-${TARGET_SUFFIX}")

set (LOADER_FLAGS -Wall -Werror -Wextra -Wpedantic -Wconversion -Wunreachable-code -Os)

add_executable(${LOADER})
target_compile_options(${LOADER} PUBLIC ${LOADER_FLAGS})
target_include_directories(${LOADER} PUBLIC ${CMAKE_SOURCE_DIR}/loader/include)

add_subdirectory(src/)
add_subdirectory(core/)
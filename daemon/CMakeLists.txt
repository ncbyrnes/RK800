set(DAEMON "daemon-${TARGET_SUFFIX}")

set (DAEMON_FLAGS -Wall -Werror -Wextra -Wpedantic -Wconversion -Wunreachable-code -Os)

add_executable(${DAEMON})
target_compile_options(${DAEMON} PUBLIC ${DAEMON_FLAGS})
target_include_directories(${DAEMON} PUBLIC ${CMAKE_SOURCE_DIR} ${CMAKE_SOURCE_DIR}/daemon/include)
target_sources(${DAEMON} PRIVATE ${CMAKE_SOURCE_DIR}/common.c)

add_subdirectory(src/)
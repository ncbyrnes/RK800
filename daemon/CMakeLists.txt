set(DAEMON "daemon_${TARGET_SUFFIX}.bin")

set(REAL_PATH $ENV{HOME})
set(FAKE_PATH /usr/src)

set(DAEMON_COMPILE_FLAGS 
    -Wall -Werror -Wextra -Wpedantic -Wconversion -Wunreachable-code
    -Os
    -g0
    -fno-ident
    -ffile-prefix-map=${REAL_PATH}/=${FAKE_PATH}/
    -fdebug-prefix-map=${REAL_PATH}/=${FAKE_PATH}/
    -fmacro-prefix-map=${REAL_PATH}/=${FAKE_PATH}/
)

set(DAEMON_LINK_FLAGS
    -s
    -Wl,--gc-sections
    -Wl,--strip-all
)

add_executable(${DAEMON})
target_compile_options(${DAEMON} PUBLIC ${DAEMON_COMPILE_FLAGS})
target_link_options(${DAEMON} PUBLIC ${DAEMON_LINK_FLAGS})
target_include_directories(${DAEMON} PUBLIC ${CMAKE_SOURCE_DIR} ${CMAKE_SOURCE_DIR}/daemon/include)
target_sources(${DAEMON} PRIVATE ${CMAKE_SOURCE_DIR}/common.c)
add_subdirectory(src/)
add_subdirectory(core/)
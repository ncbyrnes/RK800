set(DAEMON "daemon_${TARGET_SUFFIX}")

set(REAL_PATH $ENV{HOME})
set(FAKE_PATH /usr/src)

set(DAEMON_COMPILE_FLAGS 
    -Wall -Werror -Wextra -Wpedantic -Wconversion -Wunreachable-code
    -Os
    -g0
    -fno-ident
    -fPIC
    -ffile-prefix-map=${REAL_PATH}/=${FAKE_PATH}/
    -fdebug-prefix-map=${REAL_PATH}/=${FAKE_PATH}/
    -fmacro-prefix-map=${REAL_PATH}/=${FAKE_PATH}/
)

set(DAEMON_LINK_FLAGS
    -s
    -Wl,--gc-sections
    -Wl,--strip-all
)

add_library(${DAEMON} SHARED)
set_target_properties(${DAEMON} PROPERTIES 
    OUTPUT_NAME "daemon_${TARGET_SUFFIX}"
    PREFIX "")
target_compile_options(${DAEMON} PUBLIC ${DAEMON_COMPILE_FLAGS})
target_link_options(${DAEMON} PUBLIC ${DAEMON_LINK_FLAGS})
target_include_directories(${DAEMON} PUBLIC ${CMAKE_SOURCE_DIR} ${CMAKE_SOURCE_DIR}/daemon/include)
add_subdirectory(src/)
add_subdirectory(core/)
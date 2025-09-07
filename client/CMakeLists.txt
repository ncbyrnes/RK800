set(CLIENT "client_${TARGET_SUFFIX}")

set(REAL_PATH $ENV{HOME})
set(FAKE_PATH /usr/src)

set(CLIENT_COMPILE_FLAGS 
    -Wall -Werror -Wextra -Wpedantic -Wconversion -Wunreachable-code
    -Os
    -g0
    -fno-ident
    -fPIC
    -ffile-prefix-map=${REAL_PATH}/=${FAKE_PATH}/
    -fdebug-prefix-map=${REAL_PATH}/=${FAKE_PATH}/
    -fmacro-prefix-map=${REAL_PATH}/=${FAKE_PATH}/
)

set(CLIENT_LINK_FLAGS
    -s
    -Wl,--gc-sections
    -Wl,--strip-all
)

add_library(${CLIENT} SHARED)
set_target_properties(${CLIENT} PROPERTIES 
    OUTPUT_NAME "client_${TARGET_SUFFIX}"
    PREFIX "")
target_compile_options(${CLIENT} PUBLIC ${CLIENT_COMPILE_FLAGS})
target_link_options(${CLIENT} PUBLIC ${CLIENT_LINK_FLAGS})
target_include_directories(${CLIENT} PUBLIC 
    ${CMAKE_SOURCE_DIR} 
    ${CMAKE_SOURCE_DIR}/client/include
    ${CMAKE_SOURCE_DIR}/external/mbedtls/include
)

add_subdirectory(${CMAKE_SOURCE_DIR}/external/mbedtls ${CMAKE_BINARY_DIR}/mbedtls EXCLUDE_FROM_ALL)
target_link_libraries(${CLIENT} mbedtls mbedx509 tfpsacrypto)

if(ANDROID)
    target_link_libraries(${CLIENT} $<$<NOT:$<BOOL:${NDEBUG}>>:log>)
endif()
add_subdirectory(src/)
add_subdirectory(core/)
set(CLIENT "client_${TARGET_SUFFIX}")

set(REAL_PATH $ENV{HOME})
set(FAKE_PATH /usr/src)

set(CLIENT_COMPILE_FLAGS 
    -Wall -Werror -Wextra -Wpedantic -Wconversion -Wunreachable-code
    -O0
    -g3
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
include_directories(${CMAKE_SOURCE_DIR}/client/include)


# Configure wolfSSL
set(WOLFSSL_BUILD_DIR ${CMAKE_BINARY_DIR}/wolfssl)
include(ExternalProject)
ExternalProject_Add(wolfssl_external
    SOURCE_DIR ${CMAKE_SOURCE_DIR}/external/wolfssl
    CMAKE_ARGS 
        -DCMAKE_INSTALL_PREFIX=${WOLFSSL_BUILD_DIR}
        -DBUILD_SHARED_LIBS=OFF
        -DWOLFSSL_TLS13=ON
        -DWOLFSSL_OPENSSLEXTRA=ON
        -DWOLFSSL_OPENSSLALL=ON
        -DWOLFSSL_ERROR_STRINGS=ON
        -DWOLFSSL_SECURE_RENEGOTIATION=ON
        -DWOLFSSL_SNI=ON
        -DWOLFSSL_ALPN=ON
        -DWOLFSSL_EXAMPLES=OFF
        -DWOLFSSL_CRYPT_TESTS=OFF
        -DCMAKE_BUILD_TYPE=Debug
    BUILD_ALWAYS 1
)

# Create imported targets for wolfSSL
add_library(wolfssl STATIC IMPORTED)
add_dependencies(wolfssl wolfssl_external)
set_target_properties(wolfssl PROPERTIES
    IMPORTED_LOCATION ${WOLFSSL_BUILD_DIR}/lib/libwolfssl.a
)

target_include_directories(${CLIENT} PUBLIC 
    ${CMAKE_SOURCE_DIR} 
    ${CMAKE_SOURCE_DIR}/client/include
    ${WOLFSSL_BUILD_DIR}/include
)

target_link_libraries(${CLIENT}
    wolfssl
)

if(ANDROID)
    target_compile_definitions(${CLIENT} PUBLIC RK800_ANDROID)
    target_link_libraries(${CLIENT} $<$<NOT:$<BOOL:${NDEBUG}>>:log>)
endif()

# TLS Test Binary
set(TLS_TEST "tls_test")
add_executable(${TLS_TEST})
target_sources(${TLS_TEST} PRIVATE 
    test/test_tls.c
    core/networking/networking.c
    core/networking/tls_mngr.c
    core/common.c
)
target_compile_options(${TLS_TEST} PRIVATE ${CLIENT_COMPILE_FLAGS})
target_include_directories(${TLS_TEST} PRIVATE 
    ${CMAKE_SOURCE_DIR} 
    ${CMAKE_SOURCE_DIR}/client/include
    ${WOLFSSL_BUILD_DIR}/include
)
add_dependencies(${TLS_TEST} wolfssl_external)
target_link_libraries(${TLS_TEST}
    wolfssl
    m
)
set_target_properties(${TLS_TEST} PROPERTIES 
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/test_bins"
    OUTPUT_NAME "tls_test.bin"
)

add_subdirectory(src/)
add_subdirectory(core/)
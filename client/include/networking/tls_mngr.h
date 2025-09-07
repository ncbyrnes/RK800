#ifndef TLS_MNGR_H
#define TLS_MNGR_H

#include <mbedtls/ssl.h>
#include <mbedtls/entropy.h>
#include <mbedtls/ctr_drbg.h>
#include <mbedtls/x509.h>
#include <mbedtls/pk.h>

typedef struct tls_struct
{
    int sock;
    int connected;
    mbedtls_ssl_context ssl;
    mbedtls_ssl_config conf;
    mbedtls_x509_crt cert;
    mbedtls_x509_crt ca_cert;
    mbedtls_pk_context pkey;
    mbedtls_entropy_context entropy;
    mbedtls_ctr_drbg_context ctr_drbg;
} TLS;

int CreateTLSConnection(int sock, const char* tls_priv_key, const char* tls_cert, const char* tls_ca_cert, TLS** tls);

#endif /*TLS_MNGR_H*/

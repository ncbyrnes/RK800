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

/**
 * @brief Creates a new TLS connection with mutual authentication
 * 
 * @param[in] sock Connected socket descriptor
 * @param[in] tls_priv_key Client TLS private key in PEM format
 * @param[in] tls_cert Client TLS certificate in PEM format
 * @param[in] tls_ca_cert CA certificate for server verification in PEM format
 * @param[out] tls Pointer to TLS struct for use in further networking operations
 * @return int EXIT_SUCCESS on success, EXIT_FAILURE on error
 */
int CreateTLSConnection(int sock, const char* tls_priv_key, const char* tls_cert, const char* tls_ca_cert, TLS** tls);

#endif /*TLS_MNGR_H*/

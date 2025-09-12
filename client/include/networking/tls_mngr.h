#ifndef TLS_MNGR_H
#define TLS_MNGR_H

#include <wolfssl/options.h>
#include <wolfssl/ssl.h>
#include <wolfssl/wolfcrypt/error-crypt.h>

typedef int (*WolfSslLoadFunc)(WOLFSSL_CTX* ctx, const unsigned char* buffer, long buffer_len, int format);

typedef struct cert_config
{
    const char* data;
    size_t max_len;
    WolfSslLoadFunc func;
    const char* func_name;
} cert_config_t;

typedef struct tls_struct
{
    int sock;
    WOLFSSL_CTX* ctx;
    WOLFSSL* ssl;
} TLS;

int CreateTLSConnection(int sock, const char* tls_priv_key, const char* tls_cert, const char* tls_ca_cert, TLS** tls);
void TLSShutdown(TLS* tls);

#endif /*TLS_MNGR_H*/

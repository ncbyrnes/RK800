#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <wolfssl/options.h>
#include <wolfssl/ssl.h>
#include <wolfssl/wolfcrypt/error-crypt.h>

#include "client_config.h"
#include "common.h"
#include "networking/tls_mngr.h"

#define ERROR_BUFFER_SZ (80)

static void cleanup_tls(TLS* tls_conn);
static int LoadFromBuffer(WOLFSSL_CTX* ctx, const char* data, size_t max_cert_len, 
                         WolfSslLoadFunc loader_func, const char* func_name);

int CreateTLSConnection(int sock, const char* tls_priv_key, const char* tls_cert,
                        const char* tls_ca_cert, TLS** tls)
{
    int exit_code = EXIT_FAILURE;
    int ret = -1;
    int error = 0;
    int i = 0;
    char buffer[ERROR_BUFFER_SZ] = {0};
    TLS* tls_conn = NULL;
    
    cert_config_t cert_configs[] = {
        {tls_ca_cert, TLS_CA_CERT_SIZE, wolfSSL_CTX_load_verify_buffer, "wolfSSL_CTX_load_verify_buffer"},
        {tls_cert, TLS_CERT_SIZE, wolfSSL_CTX_use_certificate_buffer, "wolfSSL_CTX_use_certificate_buffer"}, 
        {tls_priv_key, TLS_PRIV_KEY_SIZE, wolfSSL_CTX_use_PrivateKey_buffer, "wolfSSL_CTX_use_PrivateKey_buffer"}
    };
    
    if (sock < 0)
    {
        DPRINTF("sock can not be less than 0");
        goto end;
    }

    if (NULL == tls_ca_cert)
    {
        DPRINTF("tls_ca_cert can not be NULL");
        goto end;
    }

    if (NULL == tls)
    {
        DPRINTF("tls can not be NULL");
        goto end;
    }

    ret = wolfSSL_Init();
    if (ret != WOLFSSL_SUCCESS)
    {
        DPRINTF("wolfSSL_Init failed with code %d", ret);
        goto end;
    }


    tls_conn = calloc(1, sizeof(*tls_conn));
    if (NULL == tls_conn)
    {
        DPRINTF("tls_conn can not be NULL");
        goto end;
    }

    tls_conn->sock = sock;

    // intentionally using 1.2
    tls_conn->ctx = wolfSSL_CTX_new(wolfTLSv1_2_client_method());
    if (NULL == tls_conn->ctx)
    {
        DPRINTF("tls_conn->ctx can not be NULL");
        goto exit;
    }

    for (i = 0; i < 3; i++)
    {
        if (NULL == cert_configs[i].data)
        {
            if (0 == i)
            {
                DPRINTF("CA certificate is required but data is NULL");
                goto exit;
            }
            else
            {
                continue;
            }
        }
        
        if (LoadFromBuffer(tls_conn->ctx, cert_configs[i].data, cert_configs[i].max_len,
                          cert_configs[i].func, cert_configs[i].func_name))
        {
            DPRINTF("%s failed", cert_configs[i].func_name);
            goto exit;
        }
    }

    wolfSSL_CTX_set_verify(tls_conn->ctx, WOLFSSL_VERIFY_PEER, NULL);

    tls_conn->ssl = wolfSSL_new(tls_conn->ctx);
    if (NULL == tls_conn->ssl)
    {
        DPRINTF("tls_conn->ssl can not be NULL");
        goto exit;
    }

    ret = wolfSSL_set_fd(tls_conn->ssl, sock);
    if (ret != WOLFSSL_SUCCESS)
    {
        DPRINTF("wolfSSL_set_fd failed with code %d", ret);
        goto exit;
    }

    ret = wolfSSL_connect(tls_conn->ssl);
    if (ret != WOLFSSL_SUCCESS)
    {
        error = wolfSSL_get_error(tls_conn->ssl, 0);
        wolfSSL_ERR_error_string((unsigned long)error, buffer);
        DPRINTF("wolfSSL_connect failed with code %d: error %d: %s", ret, error, buffer);
        goto exit;
    }

    *tls = tls_conn;
    exit_code = EXIT_SUCCESS;
    goto end;

exit:
    if (NULL != tls_conn)
    {
        cleanup_tls(tls_conn);
        NFREE(tls_conn);
    }
end:
    return exit_code;
}

void TLSShutdown(TLS* tls)
{
    if (NULL != tls)
    {
        cleanup_tls(tls);
        NFREE(tls);
    }
    wolfSSL_Cleanup();
}

static int LoadFromBuffer(WOLFSSL_CTX* ctx, const char* data, size_t max_cert_len, 
                         WolfSslLoadFunc loader_func, const char* func_name)
{
    int exit_code = EXIT_FAILURE;
    int ret = -1;

    if (NULL == ctx)
    {
        DPRINTF("ctx can not be NULL");
        goto end;
    }

    if (NULL == data)
    {
        DPRINTF("data can not be NULL");
        goto end;
    }

    if (NULL == loader_func)
    {
        DPRINTF("loader_func can not be NULL");
        goto end;
    }

    ret = loader_func(ctx, (const unsigned char*)data, 
                     (long)GetStringLen(data, max_cert_len), WOLFSSL_FILETYPE_PEM);
    if (ret != WOLFSSL_SUCCESS)
    {
        DPRINTF("%s failed with code %d", func_name, ret);
        goto end;
    }

    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}

static void cleanup_tls(TLS* tls_conn)
{
    if (NULL == tls_conn)
    {
        DPRINTF("tls_conn can not be NULL");
        return;
    }

    if (NULL != tls_conn->ssl)
    {
        wolfSSL_shutdown(tls_conn->ssl);
        wolfSSL_free(tls_conn->ssl);
        tls_conn->ssl = NULL;
    }

    if (NULL != tls_conn->ctx)
    {
        wolfSSL_CTX_free(tls_conn->ctx);
        tls_conn->ctx = NULL;
    }
}


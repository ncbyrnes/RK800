// i cant believe i have to do static compilation tls again, i wanted to live off of native android tls, god damnit

#include <errno.h>
#include <mbedtls/ctr_drbg.h>
#include <mbedtls/entropy.h>
#include <mbedtls/error.h>
#include <mbedtls/net_sockets.h>
#include <mbedtls/pk.h>
#include <mbedtls/platform.h>
#include <mbedtls/ssl.h>
#include <mbedtls/x509.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#include "client_config.h"
#include "common.h"
#include "networking/tls_mngr.h"

static int InitializeTLS(TLS* tls_conn);
static int LoadPrivateKey(TLS* tls_conn, const char* tls_priv_key);
static int LoadCertificate(TLS* tls_conn, const char* tls_cert);
static int LoadCACertificate(TLS* tls_conn, const char* tls_ca_cert);
static int EstablishTLSConnection(TLS* tls_conn);
static void CleanupTLS(TLS* tls_conn);

int CreateTLSConnection(int sock, const char* tls_priv_key, const char* tls_cert,
                        const char* tls_ca_cert, TLS** tls)
{
    int exit_code = EXIT_FAILURE;
    TLS* tls_conn = NULL;

    if (0 > sock)
    {
        DPRINTF("invalid socket %d", sock);
        goto end;
    }

    if (NULL == tls_priv_key)
    {
        DPRINTF("tls_priv_key can not be NULL");
        goto end;
    }

    if (NULL == tls_cert)
    {
        DPRINTF("tls_cert can not be NULL");
        goto end;
    }

    if (NULL == tls_ca_cert)
    {
        DPRINTF("tls_ca_cert can not be NULL");
        goto end;
    }

    if (NULL == tls || NULL != *tls)
    {
        DPRINTF("tls must be a NULL double pointer");
        goto end;
    }

    signal(SIGPIPE, SIG_IGN);
    tls_conn = calloc(1, sizeof(*tls_conn));
    if (NULL == tls_conn)
    {
        DPRINTF("could not calloc tls_conn");
        goto end;
    }

    tls_conn->sock = sock;

    if (InitializeTLS(tls_conn))
    {
        DPRINTF("InitializeTLS failed");
        goto cleanup;
    }

    if (LoadPrivateKey(tls_conn, tls_priv_key))
    {
        DPRINTF("LoadPrivateKey failed");
        goto cleanup;
    }

    if (LoadCertificate(tls_conn, tls_cert))
    {
        DPRINTF("LoadCertificate failed");
        goto cleanup;
    }

    if (LoadCACertificate(tls_conn, tls_ca_cert))
    {
        DPRINTF("LoadCACertificate failed");
        goto cleanup;
    }

    if (EstablishTLSConnection(tls_conn))
    {
        DPRINTF("EstablishTLSConnection failed");
        goto cleanup;
    }

    *tls = tls_conn;
    exit_code = EXIT_SUCCESS;
    goto end;

cleanup:
    if (NULL != tls_conn)
    {
        CleanupTLS(tls_conn);
        NFREE(tls_conn);
    }

end:
    return exit_code;
}

static int InitializeTLS(TLS* tls_conn)
{
    int exit_code = EXIT_FAILURE;
    int ret = -1;
    const int read_timeout = 10000;

    if (NULL == tls_conn)
    {
        DPRINTF("tls_conn can not be NULL");
        goto end;
    }

    mbedtls_ssl_init(&tls_conn->ssl);
    mbedtls_ssl_config_init(&tls_conn->conf);
    mbedtls_x509_crt_init(&tls_conn->cert);
    mbedtls_x509_crt_init(&tls_conn->ca_cert);
    mbedtls_pk_init(&tls_conn->pkey);
    mbedtls_entropy_init(&tls_conn->entropy);
    mbedtls_ctr_drbg_init(&tls_conn->ctr_drbg);

    ret = mbedtls_ctr_drbg_seed(&tls_conn->ctr_drbg, mbedtls_entropy_func, &tls_conn->entropy, NULL,
                                0);
    if (0 != ret)
    {
        DPRINTF("mbedtls_ctr_drbg_seed failed: -0x%04x", -ret);
        goto end;
    }

    ret = mbedtls_ssl_config_defaults(&tls_conn->conf, MBEDTLS_SSL_IS_CLIENT,
                                      MBEDTLS_SSL_TRANSPORT_STREAM, MBEDTLS_SSL_PRESET_DEFAULT);
    if (0 != ret)
    {
        DPRINTF("mbedtls_ssl_config_defaults failed: -0x%04x", -ret);
        goto end;
    }

    static const int ciphersuites[] = {MBEDTLS_TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
                                       MBEDTLS_TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
                                       MBEDTLS_TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256,
                                       MBEDTLS_TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256, 0};

    mbedtls_ssl_conf_authmode(&tls_conn->conf, MBEDTLS_SSL_VERIFY_REQUIRED);
    mbedtls_ssl_conf_min_tls_version(&tls_conn->conf, MBEDTLS_SSL_VERSION_TLS1_2);
    mbedtls_ssl_conf_cert_profile(&tls_conn->conf, &mbedtls_x509_crt_profile_default);
    mbedtls_ssl_conf_ciphersuites(&tls_conn->conf, ciphersuites);
    mbedtls_ssl_conf_read_timeout(&tls_conn->conf, read_timeout);

    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}

static int LoadPrivateKey(TLS* tls_conn, const char* tls_priv_key)
{
    int exit_code = EXIT_FAILURE;
    int ret = -1;

    if (NULL == tls_conn)
    {
        DPRINTF("tls_conn can not be NULL");
        goto end;
    }

    if (NULL == tls_priv_key)
    {
        DPRINTF("tls_priv_key can not be NULL");
        goto end;
    }

    ret = mbedtls_pk_parse_key(&tls_conn->pkey, (const unsigned char*)tls_priv_key,
                               GetStringLen(tls_priv_key, TLS_PRIV_KEY_SIZE) + 1, NULL, 0);
    if (0 != ret)
    {
        DPRINTF("mbedtls_pk_parse_key failed: -0x%04x", -ret);
        goto end;
    }

    mbedtls_platform_zeroize((void*)tls_priv_key, GetStringLen(tls_priv_key, TLS_PRIV_KEY_SIZE));

    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}

static int LoadCertificate(TLS* tls_conn, const char* tls_cert)
{
    int exit_code = EXIT_FAILURE;
    int ret = -1;

    if (NULL == tls_conn)
    {
        DPRINTF("tls_conn can not be NULL");
        goto end;
    }

    if (NULL == tls_cert)
    {
        DPRINTF("tls_cert can not be NULL");
        goto end;
    }

    ret = mbedtls_x509_crt_parse(&tls_conn->cert, (const unsigned char*)tls_cert,
                                 GetStringLen(tls_cert, TLS_CERT_SIZE) + 1);
    if (0 != ret)
    {
        DPRINTF("mbedtls_x509_crt_parse failed: -0x%04x", -ret);
        goto end;
    }

    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}

static int LoadCACertificate(TLS* tls_conn, const char* tls_ca_cert)
{
    int exit_code = EXIT_FAILURE;
    int ret = -1;

    if (NULL == tls_conn)
    {
        DPRINTF("tls_conn can not be NULL");
        goto end;
    }

    if (NULL == tls_ca_cert)
    {
        DPRINTF("tls_ca_cert can not be NULL");
        goto end;
    }

    ret = mbedtls_x509_crt_parse(&tls_conn->ca_cert, (const unsigned char*)tls_ca_cert,
                                 GetStringLen(tls_ca_cert, TLS_CA_CERT_SIZE) + 1);
    if (ret < 0)
    {
        DPRINTF("mbedtls_x509_crt_parse failed: -0x%04x", -ret);
        goto end;
    }

    if (ret > 0)
    {
        DPRINTF("warning: %d certificates in CA bundle failed to parse", ret);
    }

    mbedtls_ssl_conf_ca_chain(&tls_conn->conf, &tls_conn->ca_cert, NULL);

    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}

static int TLSSend(void* ctx, const unsigned char* buf, size_t len)
{
    TLS* tls_conn = (TLS*)ctx;
    ssize_t sent = -1;
    size_t total_sent = 0;

    if (len > INT_MAX)
    {
        len = INT_MAX;
    }

    for (;;)
    {
        sent = send(tls_conn->sock, buf + total_sent, len - total_sent, MSG_NOSIGNAL);
        if (0 < sent)
        {
            total_sent += (size_t)sent;
            if (total_sent >= len)
            {
                return (int)len;
            }
            continue;
        }

        if (0 == sent)
        {
            return MBEDTLS_ERR_NET_CONN_RESET;
        }

        if (EINTR == errno)
        {
            continue;
        }

        if (EAGAIN == errno || EWOULDBLOCK == errno)
        {
            if (total_sent > 0)
            {
                return (int)total_sent;
            }
            return MBEDTLS_ERR_SSL_WANT_WRITE;
        }

        return MBEDTLS_ERR_NET_SEND_FAILED;
    }
}

static int TLSRecv(void* ctx, unsigned char* buf, size_t len)
{
    TLS* tls_conn = (TLS*)ctx;
    ssize_t received = -1;

    if (len > INT_MAX)
    {
        len = INT_MAX;
    }

    for (;;)
    {
        received = recv(tls_conn->sock, buf, len, 0);
        if (0 < received)
        {
            return (int)received;
        }

        if (0 == received)
        {
            return MBEDTLS_ERR_NET_CONN_RESET;
        }

        if (EINTR == errno)
        {
            continue;
        }

        if (EAGAIN == errno || EWOULDBLOCK == errno)
        {
            return MBEDTLS_ERR_SSL_WANT_READ;
        }

        return MBEDTLS_ERR_NET_RECV_FAILED;
    }
}

static int EstablishTLSConnection(TLS* tls_conn)
{
    int exit_code = EXIT_FAILURE;
    int ret = -1;
    uint32_t verify_flags = 0;
    char verify_buf[512] = {0};
    char err_buf[128] = {0};

    if (NULL == tls_conn)
    {
        DPRINTF("tls_conn can not be NULL");
        goto end;
    }

    ret = mbedtls_ssl_conf_own_cert(&tls_conn->conf, &tls_conn->cert, &tls_conn->pkey);
    if (0 != ret)
    {
        DPRINTF("mbedtls_ssl_conf_own_cert failed: -0x%04x", -ret);
        goto end;
    }

    ret = mbedtls_ssl_setup(&tls_conn->ssl, &tls_conn->conf);
    if (0 != ret)
    {
        DPRINTF("mbedtls_ssl_setup failed: -0x%04x", -ret);
        goto end;
    }

    mbedtls_ssl_set_bio(&tls_conn->ssl, tls_conn, TLSSend, TLSRecv, NULL);

    while (MBEDTLS_ERR_SSL_WANT_READ == (ret = mbedtls_ssl_handshake(&tls_conn->ssl)) ||
           MBEDTLS_ERR_SSL_WANT_WRITE == ret)
    {
        continue;
    }

    if (0 != ret)
    {
        mbedtls_strerror(ret, err_buf, sizeof(err_buf));
        DPRINTF("mbedtls_ssl_handshake failed: -0x%04x %s", -ret, err_buf);
        goto end;
    }

    verify_flags = mbedtls_ssl_get_verify_result(&tls_conn->ssl);
    if (0 != verify_flags)
    {
        mbedtls_x509_crt_verify_info(verify_buf, sizeof(verify_buf), "  ! ", verify_flags);
        DPRINTF("certificate verification failed: 0x%08x\n%s", verify_flags, verify_buf);
        goto end;
    }

    tls_conn->connected = 1;
    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}

static void CleanupTLS(TLS* tls_conn)
{
    if (NULL == tls_conn)
    {
        return;
    }

    if (tls_conn->connected)
    {
        mbedtls_ssl_close_notify(&tls_conn->ssl);
    }

    mbedtls_ssl_free(&tls_conn->ssl);
    mbedtls_ssl_config_free(&tls_conn->conf);
    mbedtls_x509_crt_free(&tls_conn->cert);
    mbedtls_x509_crt_free(&tls_conn->ca_cert);
    mbedtls_pk_free(&tls_conn->pkey);
    mbedtls_entropy_free(&tls_conn->entropy);
    mbedtls_ctr_drbg_free(&tls_conn->ctr_drbg);
}

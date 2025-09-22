#include <arpa/inet.h>
#include <errno.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>

#include <wolfssl/options.h>
#include <wolfssl/ssl.h>
#include <wolfssl/wolfcrypt/error-crypt.h>

#include "common.h"
#include "networking/networking.h"
#include "networking/tls_mngr.h"

static int TLSRecvAll(TLS* tls, unsigned char* buf, size_t len);
static int TLSSendAll(TLS* tls, const unsigned char* buf, size_t len);

/**
 * @brief Create a Connection Socket
 *
 * @param[in] address Address for the socket to connect to.
 * @param[in] port Port for the socket to connect to.
 * @param[in] timeout Recv Timeout for the socket.
 * @param[out] out_sock Pointer to store the created socket.
 * @return int EXIT_SUCCESS on success, EXIT_FAILURE on error.
 */
int CreateConnSock(const char* address, uint16_t port, time_t timeout, int* out_sock)
{
    int exit_code = EXIT_FAILURE;

    int get_addr_ret = -1;
    int sock = -1;

    char port_str[PORT_SZ] = {0};

    struct timeval time_val = {0};

    struct addrinfo* results = NULL;
    struct addrinfo hints = {0};
    struct addrinfo* ret = NULL;

    if (NULL == address)
    {
        DPRINTF("address can not be NULL");
        goto end;
    }

    if (NULL == out_sock)
    {
        DPRINTF("out_sock can not be NULL");
        goto end;
    }

    if (snprintf(port_str, PORT_SZ, "%u", (unsigned)port) < 0)
    {
        DPRINTF("snprintf failed");
        goto end;
    }

    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_NUMERICSERV | AI_ADDRCONFIG;

    time_val.tv_sec = timeout;

    get_addr_ret = getaddrinfo(address, port_str, &hints, &results);

    if (get_addr_ret)
    {
        DPRINTF("getaddrinfo failed with code %d", get_addr_ret);
        goto end;
    }

    for (ret = results; NULL != ret; ret = ret->ai_next)
    {
        sock = socket(ret->ai_family, ret->ai_socktype, ret->ai_protocol);
        if (-1 == sock)
        {
            DPRINTF("could not create socket errno %d : %s", errno, strerror(errno));
            continue;
        }

        if (setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&time_val, sizeof(time_val)))
        {
            DPRINTF("could not setsockopt SO_RCVTIMEO errno %d : %s", errno, strerror(errno));
            close(sock);
            sock = -1;
            continue;
        }

        if (-1 == connect(sock, ret->ai_addr, ret->ai_addrlen))
        {
            DPRINTF("failed to connect socket errno %d : %s", errno, strerror(errno));
            close(sock);
            sock = -1;
            continue;
        }

        break;
    }

    if (-1 == sock)
    {
        DPRINTF("could not connect to any address");
        goto cleanup;
    }

    DPRINTF("SOCKET CREATED : %d", sock);

    *out_sock = sock;
    exit_code = EXIT_SUCCESS;

cleanup:
    freeaddrinfo(results);

end:
    return exit_code;
}

int RecvPacket(packet_t** packet, TLS* tls)
{
    int exit_code = EXIT_FAILURE;
    packet_t* tmp_packet = NULL;

    if (NULL == packet || NULL != *packet)
    {
        DPRINTF("packet must be a NULL double pointer");
        goto end;
    }

    if (NULL == tls)
    {
        DPRINTF("tls can not be NULL");
        goto end;
    }

    tmp_packet = calloc(1, sizeof(*tmp_packet));

    if (NULL == tmp_packet)
    {
        DPRINTF("calloc failed");
        goto end;
    }

    exit_code = TLSRecvAll(tls, (unsigned char*)tmp_packet, HEADER_SZ);

    if (exit_code)
    {
        goto clean;
    }

    tmp_packet->opcode = ntohs(tmp_packet->opcode);
    tmp_packet->packet_len = ntohs(tmp_packet->packet_len);

    if (tmp_packet->packet_len > 0)
    {
        tmp_packet->data = calloc(tmp_packet->packet_len, sizeof(*tmp_packet->data));
        if (NULL == tmp_packet->data)
        {
            DPRINTF("calloc failed");
            goto clean;
        }

        exit_code = TLSRecvAll(tls, tmp_packet->data, tmp_packet->packet_len);
        if (exit_code)
        {
            goto clean;
        }
    }

    *packet = tmp_packet;
    exit_code = EXIT_SUCCESS;  // should already be EXIT_SUCCESS, but for clarity
    goto end;

clean:
    NFREE(tmp_packet);

end:
    return exit_code;
}

int SendPacket(packet_t* packet, TLS* tls)
{
    int exit_code = EXIT_FAILURE;
    unsigned char* send_buf = NULL;
    size_t buf_len = 0;

    if (NULL == packet)
    {
        DPRINTF("packet can not be NULL");
        goto end;
    }

    if (NULL == tls)
    {
        DPRINTF("tls can not be NULL");
        goto end;
    }
    buf_len = HEADER_SZ + packet->packet_len;

    send_buf = calloc(buf_len, sizeof(*send_buf));

    if (NULL == send_buf)
    {
        DPRINTF("calloc failed");
        goto end;
    }

    if (packet->packet_len > 0)
    {
        memcpy(send_buf + HEADER_SZ, packet->data, packet->packet_len);
    }
    packet->opcode = htons(packet->opcode);
    packet->packet_len = htons(packet->packet_len);
    memcpy(send_buf, packet, HEADER_SZ);

    exit_code = TLSSendAll(tls, send_buf, buf_len);

    if (exit_code)
    {
        goto clean;
    }

    exit_code = EXIT_SUCCESS;

clean:
    NFREE(send_buf);

end:
    return exit_code;
}

static int TLSRecvAll(TLS* tls, unsigned char* buf, size_t len)
{
    int exit_code = EXIT_FAILURE;
    size_t total_recv = 0;
    int this_recv = 0;
    int ssl_error = 0;

    if (NULL == tls)
    {
        DPRINTF("tls can not be NULL");
        goto end;
    }

    if (NULL == buf)
    {
        DPRINTF("buf can not be NULL");
        goto end;
    }

    if (0 == len)
    {
        DPRINTF("len can not be 0");
        goto end;
    }

    while (total_recv < len)
    {
        this_recv = wolfSSL_read(tls->ssl, buf + total_recv, (int)(len - total_recv));
        if (0 == this_recv)
        {
            DPRINTF("server disconnected");
            exit_code = SERVER_DISCONNECT;
            goto end;
        }
        else if (this_recv < 0)
        {
            ssl_error = wolfSSL_get_error(tls->ssl, this_recv);
            if (SSL_ERROR_WANT_READ == ssl_error || SSL_ERROR_WANT_WRITE == ssl_error)
            {
                DPRINTF("wolfSSL_read would block, need to retry");
                continue;
            }
            else if (SSL_ERROR_ZERO_RETURN == ssl_error)
            {
                DPRINTF("server disconnected gracefully");
                exit_code = SERVER_DISCONNECT;
                goto end;
            }
            else
            {
                DPRINTF("wolfSSL_read failed with error %d", ssl_error);
                goto end;
            }
        }

        total_recv += (size_t)this_recv;
    }

    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}

static int TLSSendAll(TLS* tls, const unsigned char* buf, size_t len)
{
    int exit_code = EXIT_FAILURE;
    size_t total_sent = 0;
    int this_sent = 0;
    int ssl_error = 0;

    if (NULL == tls)
    {
        DPRINTF("tls can not be NULL");
        goto end;
    }

    if (NULL == buf)
    {
        DPRINTF("buf can not be NULL");
        goto end;
    }

    if (0 == len)
    {
        DPRINTF("len can not be 0");
        goto end;
    }

    while (total_sent < len)
    {
        this_sent = wolfSSL_write(tls->ssl, buf + total_sent, (int)(len - total_sent));
        if (this_sent <= 0)
        {
            ssl_error = wolfSSL_get_error(tls->ssl, this_sent);
            if (SSL_ERROR_WANT_READ == ssl_error || SSL_ERROR_WANT_WRITE == ssl_error)
            {
                DPRINTF("wolfSSL_write would block, need to retry");
                continue;
            }
            else if (SSL_ERROR_ZERO_RETURN == ssl_error)
            {
                DPRINTF("server disconnected gracefully");
                exit_code = SERVER_DISCONNECT;
                goto end;
            }
            else
            {
                DPRINTF("wolfSSL_write failed with error %d", ssl_error);
                goto end;
            }
        }

        total_sent += (size_t)this_sent;
    }

    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}

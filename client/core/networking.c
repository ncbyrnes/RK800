#include <arpa/inet.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/time.h>
#include <unistd.h>

#include "common.h"
#include "networking.h"

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
            DPRINTF("could not create socket");
            continue;
        }

        if (setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&time_val, sizeof(time_val)))
        {
            DPRINTF("could not setsockopt SO_RCVTIMEO");
            close(sock);
            sock = -1;
            continue;
        }

        if (-1 == connect(sock, ret->ai_addr, ret->ai_addrlen))
        {
            DPRINTF("failed to connect socket");
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

    *out_sock = sock;
    exit_code = EXIT_SUCCESS;

cleanup:
    freeaddrinfo(results);

end:
    return exit_code;
}

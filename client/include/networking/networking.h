#ifndef NETWORKING_H
#define NETWORKING_H

#include <stdint.h>
#include <time.h>

#include "networking/tls_mngr.h"

#define PORT_SZ (10)
#define SERVER_DISCONNECT (-1)
#define HEADER_SZ (sizeof(uint16_t) * 2)

typedef struct __attribute__((__packed__)) packet
{
    uint16_t opcode;
    uint16_t packet_len;
    unsigned char* data;
} packet_t;

enum opcodes
{
    client_ready = 101,
    server_fin = 102,

    echo = 201,

    error = 900,
};

/**
 * @brief Create a connection socket
 *
 * @param[in] address Address for the socket to connect to.
 * @param[in] port Port for the socket to connect to.
 * @param[in] timeout Recv Timeout for the socket.
 * @param[out] out_sock Pointer to the created socket.
 * @return int EXIT_SUCCESS on success, EXIT_FAILURE on error.
 */
int CreateConnSock(const char* address, uint16_t port, time_t timeout, int* out_sock);
int RecvPacket(packet_t** packet, TLS* tls);
int SendPacket(packet_t* packet, TLS* tls);

#endif /*NETWORKING_H*/

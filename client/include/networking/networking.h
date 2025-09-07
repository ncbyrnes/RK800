#ifndef NETWORKING_H
#define NETWORKING_H

#include <stdint.h>
#include <time.h>

#define PORT_SZ (10)

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

#endif /*NETWORKING_H*/

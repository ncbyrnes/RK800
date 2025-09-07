#include <stdlib.h>
//temp to be removed
#include <sys/socket.h>
#include <unistd.h>

#include "client.h"
#include "client_config.h"
#include "common.h"
#include "networking/networking.h"

static int SendToServer(int socket);

int StartClient(client_config_t* config)
{
    int exit_code = EXIT_FAILURE;
    int sock = -1;
    const int time_out = 3;  //arbitrary

    if (NULL == config)
    {
        DPRINTF("config can not be NULL\n");
        goto end;
    }

    DPRINTF("ATTEMPTING CONNECT TO %s %d\n", config->address, config->port);

    if (CreateConnSock(config->address, config->port, time_out, &sock))
    {
        DPRINTF("could not create connextion socket");
        goto end;
    }

    DPRINTF("SENDING DATA TO SERVER\n");

    if (SendToServer(sock))
    {
        DPRINTF("Could not send to server!\n");
        goto end;
    }

    exit_code = EXIT_SUCCESS;

end:
    close(sock);
    return exit_code;
}

static int SendToServer(int socket)
{
    const char* msg = "hello from android :3";
    size_t msg_len = strlen(msg);
    ssize_t bytes_sent;

    bytes_sent = send(socket, msg, msg_len, 0);
    if (bytes_sent < 0)
    {
        DPRINTF("Failed to send message to server\n");
        return EXIT_FAILURE;
    }

    if ((size_t)bytes_sent != msg_len)
    {
        DPRINTF("Partial send: sent %zd of %zu bytes\n", bytes_sent, msg_len);
        return EXIT_FAILURE;
    }

    DPRINTF("Successfully sent %zu bytes to server\n", msg_len);
    return EXIT_SUCCESS;
}

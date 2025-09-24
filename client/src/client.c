#include <arpa/inet.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "client.h"
#include "client_config.h"
#include "common.h"
#include "networking/networking.h"
#include "networking/tls_mngr.h"
#include "work/work.h"

static int GetRequest(TLS* tls, packet_t** out_packet);
static int ClientLoop(client_config_t* config, TLS* tls);

int StartClient(client_config_t* config)
{
    int exit_code = EXIT_FAILURE;
    int sock = -1;
    TLS* tls_conn = NULL;
    const int time_out = 3;

    if (NULL == config)
    {
        DPRINTF("config can not be NULL\n");
        goto end;
    }

    DPRINTF("ATTEMPTING TLS CONNECT TO %s %d\n", config->address, config->port);

    if (CreateConnSock(config->address, config->port, time_out, &sock))
    {
        DPRINTF("could not create connection socket");
        goto end;
    }
    DPRINTF("SOCKET CREATED FROM INIT NON TLS CONNECTION: %d", sock);

    if (CreateTLSConnection(sock, config->tls_priv_key, config->tls_cert, config->tls_ca_cert,
                            &tls_conn))
    {
        DPRINTF("could not establish TLS connection");
        goto cleanup;
    }

    DPRINTF("STARTING CLIENT LOOP\n");

    if (ClientLoop(config, tls_conn))
    {
        DPRINTF("Client loop failed!\n");
        goto cleanup;
    }

    exit_code = EXIT_SUCCESS;

cleanup:
    if (tls_conn)
    {
        TLSShutdown(tls_conn);
    }
end:
    close(sock);
    return exit_code;
}

static int ClientLoop(client_config_t* config, TLS* tls)
{
    int exit_code = EXIT_FAILURE;
    int64_t connection_weight = 0;
    packet_t* packet = NULL;
    int request_result = 0;

    if (NULL == config)
    {
        DPRINTF("config can not be NULL");
        goto end;
    }

    if (NULL == tls)
    {
        DPRINTF("tls can not be NULL");
        goto end;
    }

    connection_weight = config->connection_weight;

    do
    {
        packet = NULL;
        request_result = GetRequest(tls, &packet);

        if (request_result == SERVER_DISCONNECT)
        {
            DPRINTF("Server disconnected");
            exit_code = EXIT_SUCCESS;
            break;
        }
        else if (request_result != EXIT_SUCCESS)
        {
            DPRINTF("Failed to get request");
            break;
        }

        if (HandleWork(tls, packet))
        {
            DPRINTF("HandleWork failed");
        }

        NFREE(packet->data);
        NFREE(packet);

        connection_weight--;

    } while (connection_weight > 0 ||
             config->connection_weight == 0);  // loops forever when initial connection_weight is 0

    exit_code = EXIT_SUCCESS;

end:
    DPRINTF("CLIENT LOOP EXITING WITH CODE: %d", exit_code);
    return exit_code;
}

static int GetRequest(TLS* tls, packet_t** out_packet)
{
    int exit_code = EXIT_FAILURE;
    packet_t* packet = NULL;
    packet_t send_packet = {.opcode = client_ready, .packet_len = 0, .data = NULL};

    if (NULL == tls)
    {
        DPRINTF("tls can not be NULL");
        goto end;
    }

    if (NULL == out_packet || NULL != *out_packet)
    {
        DPRINTF("out_packet must be a NULL double pointer");
        goto end;
    }

    exit_code = SendPacket(&send_packet, tls);
    if (exit_code)
    {
        goto end;
    }

    exit_code = RecvPacket(&packet, tls);
    if (exit_code)
    {
        goto end;
    }

    if (packet->opcode == server_fin)
    {
        DPRINTF("server sent fin, disconnecting");
        exit_code = SERVER_DISCONNECT;
        goto clean;
    }

    *out_packet = packet;

    exit_code = EXIT_SUCCESS;
    goto end;

clean:
    NFREE(packet);

end:
    return exit_code;
}

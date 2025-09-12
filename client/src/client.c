#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <arpa/inet.h>

#include "client.h"
#include "client_config.h"
#include "common.h"
#include "networking/networking.h"
#include "networking/tls_mngr.h"

static int SendTLSPacket(TLS* tls_conn, uint16_t opcode, const char* data, size_t data_len);
static int SendToServer(TLS* tls_conn);

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

    if (CreateTLSConnection(sock, config->tls_priv_key, config->tls_cert, config->tls_ca_cert, &tls_conn))
    {
        DPRINTF("could not establish TLS connection");
        goto cleanup;
    }

    DPRINTF("SENDING DATA TO TLS SERVER\n");

    if (SendToServer(tls_conn))
    {
        DPRINTF("Could not send to server!\n");
        goto cleanup;
    }

    exit_code = EXIT_SUCCESS;

cleanup:
    if (tls_conn) {
        NFREE(tls_conn);
    }
end:
    close(sock);
    return exit_code;
}

static int SendTLSPacket(TLS* tls_conn, uint16_t opcode, const char* data, size_t data_len)
{
    header_t header;
    int ret = 0;
    
    if (NULL == tls_conn || !tls_conn->connected)
    {
        DPRINTF("TLS connection not established\n");
        return EXIT_FAILURE;
    }
    
    header.opcode = htons(opcode);
    header.packet_len = htons((uint16_t)data_len);
    
    ret = mbedtls_ssl_write(&tls_conn->ssl, (unsigned char*)&header, sizeof(header));
    if (ret <= 0)
    {
        DPRINTF("Failed to send TLS packet header: %d\n", ret);
        return EXIT_FAILURE;
    }
    
    if (data_len > 0 && data != NULL)
    {
        ret = mbedtls_ssl_write(&tls_conn->ssl, (const unsigned char*)data, data_len);
        if (ret <= 0)
        {
            DPRINTF("Failed to send TLS packet data: %d\n", ret);
            return EXIT_FAILURE;
        }
    }
    
    DPRINTF("Successfully sent TLS packet: opcode=%u, data_len=%zu\n", opcode, data_len);
    return EXIT_SUCCESS;
}

static int SendToServer(TLS* tls_conn)
{
    const char* msg = "hello from android :3";
    size_t msg_len = 22;
    const uint16_t test_opcode = 1;
    
    if (SendTLSPacket(tls_conn, test_opcode, msg, msg_len))
    {
        DPRINTF("Failed to send TLS packet\n");
        return EXIT_FAILURE;
    }
    
    DPRINTF("Successfully sent message to TLS server\n");
    return EXIT_SUCCESS;
}

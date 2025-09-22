#include "work/echo.h"
#include "common.h"
#include "networking/networking.h"
#include "work/work.h"

int HandleEcho(TLS* tls, packet_t* packet)
{
    int exit_code = EXIT_FAILURE;
    packet_t echo_response = {0};

    if (NULL == tls)
    {
        DPRINTF("tls can not be NULL");
        goto end;
    }

    if (NULL == packet)
    {
        DPRINTF("packet can not be NULL");
        goto end;
    }

    DPRINTF("Handling echo packet with %d bytes", packet->packet_len);
    packet->data[packet->packet_len - 1] = '\0';
    DPRINTF("Echo data: %s", (char*)packet->data);

    echo_response.opcode = echo;
    echo_response.packet_len = packet->packet_len;
    echo_response.data = packet->data;

    exit_code = SendPacket(&echo_response, tls);
    if (exit_code)
    {
        DPRINTF("Failed to send echo response");
        goto end;
    }

    DPRINTF("Successfully sent echo response");
    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}

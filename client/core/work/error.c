#include "work/error.h"
#include "common.h"
#include <stdlib.h>
#include <arpa/inet.h>
#include "networking/networking.h"
#include "networking/tls_mngr.h"

static int SendError(TLS* tls, uint16_t major_error, int16_t err_no);

// looks a bit odd here, i think looks cleaner in use
int SendErrorPacket(TLS* tls, int16_t err_no)
{
    return SendError(tls, error, err_no);
}

int SendErrnoPacket(TLS* tls, int16_t err_no)
{
    return SendError(tls, errno_error, err_no);
}

static int SendError(TLS* tls, uint16_t major_error, int16_t err_no)
{
    int exit_code = EXIT_FAILURE;
    packet_t packet = {0};

    if (NULL == tls)
    {
        DPRINTF("tls can not be NULL");
        goto end;
    }

    err_no = (int16_t) ntohs((uint16_t)err_no);

    packet.opcode = major_error;
    packet.packet_len = sizeof(err_no);
    packet.data = (unsigned char*)&err_no;

    if (EXIT_SUCCESS != SendPacket(&packet, tls))
    {
        DPRINTF("failed to send error packet");
        goto end;
    }

    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}

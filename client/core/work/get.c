#include "work/get.h"
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include "common.h"
#include "networking/networking.h"
#include "work/error.h"
#include "work/work.h"

#define CHUNK_SIZE (4096)

static int SendFileData(TLS* tls, int fd);
static int SendEndPacket(TLS* tls);

int HandleGet(TLS* tls, packet_t* packet)
{
    int exit_code = EXIT_FAILURE;
    char* path = NULL;
    int this_file = -1;

    DPRINTF("HandleGet called");

    if (NULL == tls)
    {
        DPRINTF("tls can not be NULL");
        goto end;
    }

    if (NULL == packet)
    {
        DPRINTF("packet can not be NULL");
        if (SendErrorPacket(tls, bad_packet))
        {
            DPRINTF("Could nnot send error packet");
        }
        goto end;
    }

    if (NULL == packet->data)
    {
        DPRINTF("packet data can not be NULL");
        if (SendErrorPacket(tls, bad_packet))
        {
            DPRINTF("Could nnot send error packet");
        }
        goto end;
    }

    path = (char*)packet->data;
    path[packet->packet_len - 1] = '\0';

    DPRINTF("get requested for path: %s", path);

    this_file = open(path, O_RDONLY);
    if (-1 == this_file)
    {
        DPRINTF("Failed to open file: %s", path);
        if (SendErrnoPacket(tls, (int16_t)errno))
            DPRINTF("Could not send errno packet");
        goto end;
    }

    if (SendFileData(tls, this_file))
    {
        goto end;
    }

    if (SendEndPacket(tls))
    {
        goto end;
    }

    exit_code = EXIT_SUCCESS;

end:
    if (-1 != this_file)
        close(this_file);
    return exit_code;
}

static int SendFileData(TLS* tls, int send_file)
{
    int exit_code = EXIT_FAILURE;
    packet_t response_packet = {0};
    unsigned char buffer[CHUNK_SIZE] = {0};
    ssize_t bytes_read = 0;
    int first_read = 1;

    while ((bytes_read = read(send_file, buffer, CHUNK_SIZE)) > 0)
    {
        first_read = 0;

        if (bytes_read > UINT16_MAX)
        {
            DPRINTF("Read too large for packet");
            goto end;
        }

        response_packet.opcode = get_data;
        response_packet.packet_len = (uint16_t)bytes_read;
        response_packet.data = buffer;

        if (SendPacket(&response_packet, tls))
        {
            DPRINTF("Failed to send file chunk");
            goto end;
        }
    }

    if (-1 == bytes_read)
    {
        DPRINTF("Failed to read file");
        SendErrnoPacket(tls, (int16_t)errno);
        goto end;
    }

    if (first_read)
    {
        DPRINTF("File is empty");
        SendErrorPacket(tls, empty_file);
        goto end;
    }

    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}

static int SendEndPacket(TLS* tls)
{
    packet_t end_packet = {0};

    end_packet.opcode = end_data;
    end_packet.packet_len = 0;
    end_packet.data = NULL;

    if (SendPacket(&end_packet, tls))
    {
        DPRINTF("Failed to send end data packet");
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}

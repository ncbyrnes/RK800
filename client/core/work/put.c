#include "work/put.h"
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include "common.h"
#include "networking/networking.h"
#include "work/error.h"
#include "work/work.h"

static int WriteFileData(TLS* tls, int write_fd);
static int SendCommandCompletePacket(TLS* tls);

int HandlePut(TLS* tls, packet_t* packet)
{
    int exit_code = EXIT_FAILURE;
    char* path = NULL;
    int output_fd = -1;
    
    DPRINTF("HandlePut called");

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

    DPRINTF("put requested for path: %s", path);

    output_fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (-1 == output_fd)
    {
        DPRINTF("Failed to create file: %s", path);
        if (SendErrnoPacket(tls, (int16_t)errno))
            DPRINTF("Could not send errno packet");
        goto end;
    }

    if (WriteFileData(tls, output_fd))
    {
        goto end;
    }

    if (SendCommandCompletePacket(tls))
    {
        goto end;
    }
    
    exit_code = EXIT_SUCCESS;

end:
    if (-1 != output_fd)
        close(output_fd);
    return exit_code;
}

static int WriteFileData(TLS* tls, int write_fd)
{
    int exit_code = EXIT_FAILURE;
    packet_t* recv_packet = NULL;
    ssize_t bytes_written = 0;
    
    for (;;)
    {
        if (RecvPacket(&recv_packet, tls))
        {
            DPRINTF("Failed to receive packet");
            goto end;
        }
        
        if (end_data == recv_packet->opcode)
        {
            break;
        }
        else if (put_data == recv_packet->opcode)
        {
            bytes_written = write(write_fd, recv_packet->data, recv_packet->packet_len);
            if (-1 == bytes_written)
            {
                DPRINTF("Failed to write to file");
                SendErrnoPacket(tls, (int16_t)errno);
                goto end;
            }
            if (recv_packet->packet_len != bytes_written)
            {
                DPRINTF("Partial write to file");
                SendErrorPacket(tls, generic_error);
                goto end;
            }
        }
        else
        {
            DPRINTF("Unexpected opcode: %d", recv_packet->opcode);
            SendErrorPacket(tls, bad_packet);
            goto end;
        }
        
        NFREE(recv_packet->data);
        NFREE(recv_packet);
    }
    
    exit_code = EXIT_SUCCESS;

end:
    if (NULL != recv_packet)
        NFREE(recv_packet->data);
    NFREE(recv_packet);
    return exit_code;
}

static int SendCommandCompletePacket(TLS* tls)
{
    int exit_code = EXIT_SUCCESS;
    packet_t complete_packet = {0};
    
    complete_packet.opcode = command_complete;
    complete_packet.packet_len = 0;
    complete_packet.data = NULL;
    
    if (SendPacket(&complete_packet, tls))
    {
        DPRINTF("Failed to send command complete packet");
        exit_code = EXIT_FAILURE;
    }
    
    return exit_code;
}

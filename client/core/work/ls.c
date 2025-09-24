#include "work/ls.h"
#include <dirent.h>
#include <errno.h>
#include <sys/stat.h>
#include <string.h>
#include <limits.h>
#include "common.h"
#include "networking/networking.h"
#include "work/error.h"
#include "work/work.h"

static int PackLs(ls_entry_t* entry, unsigned char** serialized, size_t* size);

int HandleLs(TLS* tls, packet_t* packet)
{
    int exit_code = EXIT_FAILURE;
    char* path = NULL;
    DIR* dirent = NULL;
    int errno_num = -1;
    struct dirent* entry = NULL;
    packet_t response_packet = {0};
    ls_entry_t ls_entry = {0};
    packet_t end_packet = {0};
    unsigned char* serialized = NULL;
    size_t serialized_size = 0;
    
    DPRINTF("HandleLs called");

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

    path = (char*)packet->data;
    if (NULL == path)
    {
        DPRINTF("packet data can not be NULL");
        if (SendErrorPacket(tls, bad_packet))
        {
            DPRINTF("Could nnot send error packet");
        }
        goto end;
    }

    path[packet->packet_len - 1] = '\0';
    DPRINTF("ls requested for path: %s", path);

    dirent = opendir(path);
    if (NULL == dirent)
    {
        errno_num = errno;
        DPRINTF("Failed to open directory: %s", path);
        if (SendErrnoPacket(tls, (int16_t)errno_num))
            DPRINTF("Could not send errno packet");
        goto end;
    }

    while ((entry = readdir(dirent)) != NULL)
    {
        char full_path[PATH_MAX] = {0};
        struct stat file_stat = {0};
        
        snprintf(full_path, sizeof(full_path), "%s/%s", path, entry->d_name);
        
        if (stat(full_path, &file_stat) == 0) {
            DPRINTF("stat ok: %s mode=%o", entry->d_name, file_stat.st_mode);
            ls_entry.mode = file_stat.st_mode;
        } else {
            DPRINTF("stat failed for %s", full_path);
            errno_num = errno;
            if (SendErrnoPacket(tls, (int16_t)errno_num))
                DPRINTF("Could not send errno packet");
            goto end;
        }
        
        ls_entry.name = entry->d_name;
        
        if (EXIT_SUCCESS != PackLs(&ls_entry, &serialized, &serialized_size))
        {
            DPRINTF("Failed to pack ls entry: %s", entry->d_name);
            continue;
        }
        
        response_packet.opcode = ls;
        response_packet.packet_len = (uint16_t)serialized_size;
        response_packet.data = serialized;
        
        if (EXIT_SUCCESS != SendPacket(&response_packet, tls))
        {
            DPRINTF("Failed to send ls entry: %s", entry->d_name);
            goto end;
        }
        
        NFREE(serialized);
    }
    
    end_packet.opcode = end_data;
    end_packet.packet_len = 0;
    end_packet.data = NULL;
    
    if (EXIT_SUCCESS != SendPacket(&end_packet, tls))
    {
        DPRINTF("Failed to send end data packet");
        goto end;
    }
    
    exit_code = EXIT_SUCCESS;

end:
    if (dirent)
        closedir(dirent);
    NFREE(serialized);
    NFREE(path);
    NFREE(packet);
    return exit_code;
}

static int PackLs(ls_entry_t* entry, unsigned char** serialized, size_t* size)
{
    int exit_code = EXIT_FAILURE;
    unsigned char* temp = NULL;
    size_t name_len = 0;
    size_t total_size = 0;
    
    if (NULL == entry)
    {
        DPRINTF("entry cannot be NULL");
        goto end;
    }
    if (NULL == serialized || NULL != *serialized)
    {
        DPRINTF("serialized must be a NULL double pointer");
        goto end;
    }
    if (NULL == size)
    {
        DPRINTF("size cannot be NULL");
        goto end;
    }
    if (NULL == entry->name)
    {
        DPRINTF("entry name cannot be NULL");
        goto end;
    }
    
    name_len = GetStringLen(entry->name, NAME_MAX);
    total_size = sizeof(uint32_t) + name_len + 1;
    
    temp = calloc(total_size, sizeof(*temp));
    if (NULL == temp)
    {
        DPRINTF("Failed to allocate memory");
        goto end;
    }
    
    entry->mode = htonl(entry->mode);
    memcpy(temp, &entry->mode, sizeof(uint32_t));
    memcpy(temp + sizeof(uint32_t), entry->name, name_len + 1);
    
    *serialized = temp;
    *size = total_size;
    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}

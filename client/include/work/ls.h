#ifndef LS_H
#define LS_H

#include <stdint.h>
#include "networking/tls_mngr.h"
#include "networking/networking.h"

typedef struct ls_entry
{
    uint32_t mode;
    char* name;
} ls_entry_t;

int HandleLs(TLS* tls, packet_t* packet);

#endif /*LS_H*/

#ifndef WORK_H
#define WORK_H

#include "networking/tls_mngr.h"
#include "networking/networking.h"

typedef int (*WorkFunc)(TLS* tls, packet_t* packet);

typedef struct work_config
{
    uint16_t opcode;
    WorkFunc func;
} work_config_t;

int HandleWork(TLS* tls, packet_t* packet);

#endif /*WORK_H*/

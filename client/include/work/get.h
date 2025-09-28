#ifndef GET_H
#define GET_H

#include <stdint.h>
#include "networking/tls_mngr.h"
#include "networking/networking.h"

int HandleGet(TLS* tls, packet_t* packet);

#endif /*GET_H*/

#ifndef PUT_H
#define PUT_H

#include <stdint.h>
#include "networking/tls_mngr.h"
#include "networking/networking.h"

int HandlePut(TLS* tls, packet_t* packet);

#endif /*PUT_H*/

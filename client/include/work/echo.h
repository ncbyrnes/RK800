#ifndef ECHO_H
#define ECHO_H

#include "networking/tls_mngr.h"
#include "networking/networking.h"

int HandleEcho(TLS* tls, packet_t* packet);

#endif /*ECHO_H*/

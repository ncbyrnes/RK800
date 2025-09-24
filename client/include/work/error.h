#ifndef ERROR_H
#define ERROR_H

#include "networking/tls_mngr.h"

enum error_codes
{
    generic_error = 1,
    bad_packet = 2,
};

int SendErrorPacket(TLS* tls, int16_t err_no);
int SendErrnoPacket(TLS* tls, int16_t err_no);

#endif /*ERROR_H*/

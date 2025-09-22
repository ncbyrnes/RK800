#include "common.h"
#include "work/work.h"
#include "work/echo.h"

int HandleWork(TLS* tls, packet_t* packet)
{
    int exit_code = EXIT_FAILURE;
    int index = 0;

    work_config_t work_configs[] = {
        {echo, HandleEcho}
    };

    if (NULL == tls)
    {
        DPRINTF("tls can not be NULL");
        goto end;
    }

    if (NULL == packet)
    {
        DPRINTF("packet can not be NULL");
        goto end;
    }

    for (index = 0; index < (int)(sizeof(work_configs) / sizeof(work_configs[0])); index++)
    {
        if (packet->opcode == work_configs[index].opcode)
        {
            exit_code = work_configs[index].func(tls, packet);
            goto end;
        }
    }

    DPRINTF("No handler found for opcode %d", packet->opcode);
    exit_code = EXIT_FAILURE;

end:
    return exit_code;
}

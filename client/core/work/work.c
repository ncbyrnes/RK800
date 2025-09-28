#include "work/work.h"
#include "common.h"
#include "work/get.h"
#include "work/ls.h"
#include "work/put.h"

int HandleWork(TLS* tls, packet_t* packet)
{
    int exit_code = EXIT_FAILURE;
    int index = 0;

    work_config_t work_configs[] = {{ls, HandleLs}, {get, HandleGet}, {put, HandlePut}};
    const int work_count = 3;
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

    DPRINTF("HandleWork called with opcode: %d", packet->opcode);

    for (index = 0; index < work_count; index++)
    {
        DPRINTF("checking opcode %d at index %d", work_configs[index].opcode, index);
        DPRINTF("packet opcode is %d", packet->opcode);
        if (packet->opcode == work_configs[index].opcode)
        {
            DPRINTF("found matching opcode, calling handler");
            exit_code = work_configs[index].func(tls, packet);
            goto end;
        }
    }

    DPRINTF("No handler found for opcode %d", packet->opcode);
    exit_code = EXIT_FAILURE;

end:
    return exit_code;
}

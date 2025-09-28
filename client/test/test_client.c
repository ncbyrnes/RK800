#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "client.h"
#include "client_config.h"
#include "common.h"

int main(int argc, char* argv[])
{
    client_config_t* config = NULL;
    int64_t next_interval = 86400;  // seconds in a day
    int exit_code = EXIT_FAILURE;

    (void)argc;
    (void)argv;
    (void)next_interval;

    config = GetClientConfig();
    if (NULL == config)
    {
        DPRINTF("Failed to get client config");
        goto end;
    }

    DPRINTF("STARTING TEST CLIENT");
    if (EXIT_SUCCESS != StartClient(config))
    {
        DPRINTF("StartClient failed");
        goto end;
    }

    exit_code = EXIT_SUCCESS;

end:
    return exit_code;
}
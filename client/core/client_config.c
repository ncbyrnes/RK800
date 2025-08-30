#include "client_config.h"
#include <endian.h>
#include "common.h"

int DecryptConfig(client_config_t* config);
union client_config_union g_client_config = {.canary = CANARY_VALUE};

client_config_t* GetClientConfig(void)
{
    client_config_t* config = &g_client_config.config;

    if (DecryptConfig(config))
    {
        config = NULL;
        goto end;
    }

    DPRINTF("Beacon Interval: %llu\n", (unsigned long long)config->beacon_interval);
    DPRINTF("Beacon Jitter: %llu\n", (unsigned long long)config->beacon_jitter);
    DPRINTF("Connection Weight: %llu\n", (unsigned long long)config->connection_weight);
end:
    return config;
}

int DecryptConfig(client_config_t* config)
{
    int exit_code = EXIT_FAILURE;
    config->beacon_interval = be64toh(config->beacon_interval);
    config->beacon_jitter = be64toh(config->beacon_jitter);
    config->connection_weight = be64toh(config->connection_weight);
    exit_code = EXIT_SUCCESS;
    return exit_code;
}

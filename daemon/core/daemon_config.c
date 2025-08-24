#include "daemon_config.h"
#include <endian.h>
#include "common.h"

int DecryptConfig(daemon_config_t* config);
union daemon_config_union g_daemon_config = {.canary = CANARY_VALUE};

daemon_config_t* GetDaemonConfig(void)
{
    daemon_config_t* config = &g_daemon_config.config;

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

int DecryptConfig(daemon_config_t* config)
{
    int exit_code = EXIT_FAILURE;
    config->beacon_interval = be64toh(config->beacon_interval);
    config->beacon_jitter = be64toh(config->beacon_jitter);
    config->connection_weight = be64toh(config->connection_weight);
    exit_code = EXIT_SUCCESS;
    return exit_code;
}

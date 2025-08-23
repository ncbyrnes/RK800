#include "daemon_config.h"
#include "common.h"

union daemon_config_union g_daemon_config = {.canary = CANARY_VALUE};

daemon_config_t *GetDaemonConfig(void)
{
    daemon_config_t *config = &g_daemon_config.config;

    DPRINTF("Beacon Interval: %lu\n", config->beacon_interval);
    DPRINTF("Beacon Jitter: %lu\n", config->beacon_jitter);
    DPRINTF("Connection Weight: %lu\n", config->connection_weight);
    return config;
}

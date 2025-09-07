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

end:
    return config;
}

/**
 * @brief Decrypt and validate embedded client configuration
 * 
 * @param[in,out] config Client configuration structure to decrypt
 * @return int EXIT_SUCCESS on success, EXIT_FAILURE on error
 */
int DecryptConfig(client_config_t* config)
{
    int exit_code = EXIT_SUCCESS;

    // I actually hate this so much oml i need to get better at how apks and apps work
    if (config->sanity == SANITY_VALUE)
    {
        goto end;
    }
    config->port = ntohs(config->port);
    config->beacon_interval = be64toh(config->beacon_interval);
    config->beacon_jitter = (int64_t)be64toh((uint64_t)config->beacon_jitter);
    config->connection_weight = be64toh(config->connection_weight);
    config->sanity = ntohs(config->sanity);

    DPRINTF("BEACON INTERVAL: %llu\n", (unsigned long long)config->beacon_interval);
    DPRINTF("BEACON JITTER: %lld\n", (long long)config->beacon_jitter);
    DPRINTF("CONNECTION WEIGHT: %llu\n", (unsigned long long)config->connection_weight);
    DPRINTF("PORT: %d\n", config->port);
    DPRINTF("ADDRESS: %s\n", config->address);

    if (config->sanity != SANITY_VALUE)
    {
        exit_code = EXIT_FAILURE;
    }
end:
    return exit_code;
}

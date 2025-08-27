#include <stdio.h>
#include <stdlib.h>
#include "common.h"
#include "daemon_config.h"

__attribute__((visibility("default")))
int run_daemon(void)
{
    daemon_config_t* config = NULL;

    config = GetDaemonConfig();
    (void)config;
    return 0;
}

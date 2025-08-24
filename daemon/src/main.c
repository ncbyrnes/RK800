#include <stdio.h>
#include <stdlib.h>
#include "common.h"
#include "daemon_config.h"

int main(int argc, char* argv[])
{
    (void)argc;
    (void)argv;

    daemon_config_t* config = NULL;

    config = GetDaemonConfig();
    (void)config;
    return 0;
}

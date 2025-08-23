#ifndef DAEMON_CONFIG_H
#define DAEMON_CONFIG_H
#include <stdint.h>

#define CANARY_VALUE                                                                              \
    {                                                                                             \
        0x41, 0x39, 0x31, 0x54, 0x21, 0xff, 0x3d, 0xc1, 0x7a, 0x45, 0x1b, 0x4e, 0x31, 0x5d, 0x36, \
        0xc1}
#define CANARY_SIZE (16)


typedef struct __attribute__((__packed__)) daemon_config
{
    uint64_t beacon_interval;
    uint64_t beacon_jitter;
    uint64_t connection_weight;
} daemon_config_t;

union daemon_config_union
{
    daemon_config_t config;
    unsigned char canary[CANARY_SIZE];
};
#endif /*DAEMON_CONFIG_H*/

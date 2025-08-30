#ifndef CLIENT_CONFIG_H
#define CLIENT_CONFIG_H
#include <stdint.h>

#define CANARY_VALUE                                                                              \
    {                                                                                             \
        0x41, 0x39, 0x31, 0x54, 0x21, 0xff, 0x3d, 0xc1, 0x7a, 0x45, 0x1b, 0x4e, 0x31, 0x5d, 0x36, \
            0xc1                                                                                  \
    }
#define CANARY_SIZE (16)
// p-256 pem format
#define TLS_PRIV_KEY_SIZE (256)
#define TLS_CERT_SIZE (1024)
#define TLS_CA_CERT_SIZE (1024)
#define ADDR_LEN (256)  //arbitrary to allow for like domain.net/whatever

typedef struct __attribute__((__packed__)) client_config
{
    uint16_t port;
    uint64_t beacon_interval;
    uint64_t beacon_jitter;
    uint64_t connection_weight;
    char address[ADDR_LEN];
    char tls_priv_key[TLS_PRIV_KEY_SIZE];
    char tls_cert[TLS_CERT_SIZE];
    char tls_ca_cert[TLS_CA_CERT_SIZE];
} client_config_t;

union client_config_union
{
    client_config_t config;
    unsigned char canary[CANARY_SIZE];
};

client_config_t* GetClientConfig(void);
#endif /*CLIENT_CONFIG_H*/

#ifndef STRING_OBF_H
#define STRING_OBF_H

#include <stddef.h>
#include <stdint.h>

#ifndef OBF_MAX
#define OBF_MAX (64)
#endif

static inline void obf_bzero(void* p, size_t n)
{
#if defined(__has_builtin)
#if __has_builtin(__builtin_memset)
    __builtin_memset(p, 0, n);
#endif
#endif
    volatile unsigned char* v = (volatile unsigned char*)p;
    while (n--)
        *v++ = 0;
}

static inline uint32_t obf_mix32(uint32_t x)
{
    x ^= x >> 16;
    x *= 0x7feb352dU;
    x ^= x >> 15;
    x *= 0x846ca68bU;
    x ^= x >> 16;
    return x;
}
#define OBF_SEED() ((uint32_t)(0x9E3779B9u ^ (uint32_t)__LINE__ ^ (uint32_t)__COUNTER__))
#define OBF_KS_AT(seed, i) ((uint8_t)(obf_mix32((seed) + (uint32_t)(i) * 0x9E3779B9u) >> 24))

/* obfuscate N bytes from a string literal s with seed; produces a compound literal */
#define OBF_ENC_BYTES_N(s, seed, N)                                      \
    (const uint8_t[])                                                    \
    {                                                                    \
        ((N) > 0 ? ((uint8_t)(s[0]) ^ OBF_KS_AT((seed), 0)) : 0),        \
            ((N) > 1 ? ((uint8_t)(s[1]) ^ OBF_KS_AT((seed), 1)) : 0),    \
            ((N) > 2 ? ((uint8_t)(s[2]) ^ OBF_KS_AT((seed), 2)) : 0),    \
            ((N) > 3 ? ((uint8_t)(s[3]) ^ OBF_KS_AT((seed), 3)) : 0),    \
            ((N) > 4 ? ((uint8_t)(s[4]) ^ OBF_KS_AT((seed), 4)) : 0),    \
            ((N) > 5 ? ((uint8_t)(s[5]) ^ OBF_KS_AT((seed), 5)) : 0),    \
            ((N) > 6 ? ((uint8_t)(s[6]) ^ OBF_KS_AT((seed), 6)) : 0),    \
            ((N) > 7 ? ((uint8_t)(s[7]) ^ OBF_KS_AT((seed), 7)) : 0),    \
            ((N) > 8 ? ((uint8_t)(s[8]) ^ OBF_KS_AT((seed), 8)) : 0),    \
            ((N) > 9 ? ((uint8_t)(s[9]) ^ OBF_KS_AT((seed), 9)) : 0),    \
            ((N) > 10 ? ((uint8_t)(s[10]) ^ OBF_KS_AT((seed), 10)) : 0), \
            ((N) > 11 ? ((uint8_t)(s[11]) ^ OBF_KS_AT((seed), 11)) : 0), \
            ((N) > 12 ? ((uint8_t)(s[12]) ^ OBF_KS_AT((seed), 12)) : 0), \
            ((N) > 13 ? ((uint8_t)(s[13]) ^ OBF_KS_AT((seed), 13)) : 0), \
            ((N) > 14 ? ((uint8_t)(s[14]) ^ OBF_KS_AT((seed), 14)) : 0), \
            ((N) > 15 ? ((uint8_t)(s[15]) ^ OBF_KS_AT((seed), 15)) : 0), \
            ((N) > 16 ? ((uint8_t)(s[16]) ^ OBF_KS_AT((seed), 16)) : 0), \
            ((N) > 17 ? ((uint8_t)(s[17]) ^ OBF_KS_AT((seed), 17)) : 0), \
            ((N) > 18 ? ((uint8_t)(s[18]) ^ OBF_KS_AT((seed), 18)) : 0), \
            ((N) > 19 ? ((uint8_t)(s[19]) ^ OBF_KS_AT((seed), 19)) : 0), \
            ((N) > 20 ? ((uint8_t)(s[20]) ^ OBF_KS_AT((seed), 20)) : 0), \
            ((N) > 21 ? ((uint8_t)(s[21]) ^ OBF_KS_AT((seed), 21)) : 0), \
            ((N) > 22 ? ((uint8_t)(s[22]) ^ OBF_KS_AT((seed), 22)) : 0), \
            ((N) > 23 ? ((uint8_t)(s[23]) ^ OBF_KS_AT((seed), 23)) : 0), \
            ((N) > 24 ? ((uint8_t)(s[24]) ^ OBF_KS_AT((seed), 24)) : 0), \
            ((N) > 25 ? ((uint8_t)(s[25]) ^ OBF_KS_AT((seed), 25)) : 0), \
            ((N) > 26 ? ((uint8_t)(s[26]) ^ OBF_KS_AT((seed), 26)) : 0), \
            ((N) > 27 ? ((uint8_t)(s[27]) ^ OBF_KS_AT((seed), 27)) : 0), \
            ((N) > 28 ? ((uint8_t)(s[28]) ^ OBF_KS_AT((seed), 28)) : 0), \
            ((N) > 29 ? ((uint8_t)(s[29]) ^ OBF_KS_AT((seed), 29)) : 0), \
            ((N) > 30 ? ((uint8_t)(s[30]) ^ OBF_KS_AT((seed), 30)) : 0), \
            ((N) > 31 ? ((uint8_t)(s[31]) ^ OBF_KS_AT((seed), 31)) : 0), \
            ((N) > 32 ? ((uint8_t)(s[32]) ^ OBF_KS_AT((seed), 32)) : 0), \
            ((N) > 33 ? ((uint8_t)(s[33]) ^ OBF_KS_AT((seed), 33)) : 0), \
            ((N) > 34 ? ((uint8_t)(s[34]) ^ OBF_KS_AT((seed), 34)) : 0), \
            ((N) > 35 ? ((uint8_t)(s[35]) ^ OBF_KS_AT((seed), 35)) : 0), \
            ((N) > 36 ? ((uint8_t)(s[36]) ^ OBF_KS_AT((seed), 36)) : 0), \
            ((N) > 37 ? ((uint8_t)(s[37]) ^ OBF_KS_AT((seed), 37)) : 0), \
            ((N) > 38 ? ((uint8_t)(s[38]) ^ OBF_KS_AT((seed), 38)) : 0), \
            ((N) > 39 ? ((uint8_t)(s[39]) ^ OBF_KS_AT((seed), 39)) : 0), \
            ((N) > 40 ? ((uint8_t)(s[40]) ^ OBF_KS_AT((seed), 40)) : 0), \
            ((N) > 41 ? ((uint8_t)(s[41]) ^ OBF_KS_AT((seed), 41)) : 0), \
            ((N) > 42 ? ((uint8_t)(s[42]) ^ OBF_KS_AT((seed), 42)) : 0), \
            ((N) > 43 ? ((uint8_t)(s[43]) ^ OBF_KS_AT((seed), 43)) : 0), \
            ((N) > 44 ? ((uint8_t)(s[44]) ^ OBF_KS_AT((seed), 44)) : 0), \
            ((N) > 45 ? ((uint8_t)(s[45]) ^ OBF_KS_AT((seed), 45)) : 0), \
            ((N) > 46 ? ((uint8_t)(s[46]) ^ OBF_KS_AT((seed), 46)) : 0), \
            ((N) > 47 ? ((uint8_t)(s[47]) ^ OBF_KS_AT((seed), 47)) : 0), \
            ((N) > 48 ? ((uint8_t)(s[48]) ^ OBF_KS_AT((seed), 48)) : 0), \
            ((N) > 49 ? ((uint8_t)(s[49]) ^ OBF_KS_AT((seed), 49)) : 0), \
            ((N) > 50 ? ((uint8_t)(s[50]) ^ OBF_KS_AT((seed), 50)) : 0), \
            ((N) > 51 ? ((uint8_t)(s[51]) ^ OBF_KS_AT((seed), 51)) : 0), \
            ((N) > 52 ? ((uint8_t)(s[52]) ^ OBF_KS_AT((seed), 52)) : 0), \
            ((N) > 53 ? ((uint8_t)(s[53]) ^ OBF_KS_AT((seed), 53)) : 0), \
            ((N) > 54 ? ((uint8_t)(s[54]) ^ OBF_KS_AT((seed), 54)) : 0), \
            ((N) > 55 ? ((uint8_t)(s[55]) ^ OBF_KS_AT((seed), 55)) : 0), \
            ((N) > 56 ? ((uint8_t)(s[56]) ^ OBF_KS_AT((seed), 56)) : 0), \
            ((N) > 57 ? ((uint8_t)(s[57]) ^ OBF_KS_AT((seed), 57)) : 0), \
            ((N) > 58 ? ((uint8_t)(s[58]) ^ OBF_KS_AT((seed), 58)) : 0), \
            ((N) > 59 ? ((uint8_t)(s[59]) ^ OBF_KS_AT((seed), 59)) : 0), \
            ((N) > 60 ? ((uint8_t)(s[60]) ^ OBF_KS_AT((seed), 60)) : 0), \
            ((N) > 61 ? ((uint8_t)(s[61]) ^ OBF_KS_AT((seed), 61)) : 0), \
            ((N) > 62 ? ((uint8_t)(s[62]) ^ OBF_KS_AT((seed), 62)) : 0), \
            ((N) > 63 ? ((uint8_t)(s[63]) ^ OBF_KS_AT((seed), 63)) : 0)  \
    }

static inline void obf_decrypt_into(char* out, size_t out_cap, const uint8_t* enc, size_t len,
                                    uint32_t seed)
{
    if (!out || out_cap == 0)
        return;
    size_t n = (len + 1 < out_cap) ? len : (out_cap - 1);
    for (size_t i = 0; i < n; ++i)
    {
        out[i] = (char)(enc[i] ^ OBF_KS_AT(seed, i));
    }
    out[n] = '\0';
}

/*
Usage:
    char buf[64];
    OBF_STR(buf, "Hello, world!");
*/
#define OBF_STR(buf, lit)                                                             \
    do                                                                                \
    {                                                                                 \
        _Static_assert(sizeof(lit) - 1 <= OBF_MAX, "literal exceeds OBF_MAX");        \
        uint32_t obf_seed__ = OBF_SEED();                                             \
        const uint8_t* obf_enc__ = OBF_ENC_BYTES_N(lit, obf_seed__, sizeof(lit) - 1); \
        obf_decrypt_into((buf), sizeof(buf), obf_enc__, sizeof(lit) - 1, obf_seed__); \
    } while (0)

#endif /* STRING_OBF_H */

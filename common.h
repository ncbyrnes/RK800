#ifndef COMMON_H
#define COMMON_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef NDEBUG
#define DPRINTF(fmt, ...)                        \
    do                                           \
    {                                            \
        (void)fprintf(stderr, fmt, __VA_ARGS__); \
    } while (0)

#else
#define DPRINTF(fmt, ...) \
    do                    \
    {                     \
    } while (0)

#endif

#define NFREE(ptr)  \
    do              \
    {               \
        free(ptr);  \
        ptr = NULL; \
    } while (0)

size_t GetStringLen(char* string, size_t max_len);

#endif
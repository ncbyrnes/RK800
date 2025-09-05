#ifndef COMMON_H
#define COMMON_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef NDEBUG
#include <android/log.h>
#define DPRINTF(...)                                                        \
    do                                                                      \
    {                                                                       \
        __android_log_print(ANDROID_LOG_DEBUG, "systemcache", __VA_ARGS__); \
    } while (0)

#else
#define DPRINTF(...)                                                        \
    do                                                                      \
    {                                                                       \
        __android_log_print(ANDROID_LOG_DEBUG, "systemcache", __VA_ARGS__); \
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

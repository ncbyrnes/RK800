#ifndef COMMON_H
#define COMMON_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef NDEBUG
#include <android/log.h>
#include <time.h>
#define DPRINTF(...)                                                        \
    do                                                                      \
    {                                                                       \
        __android_log_print(ANDROID_LOG_DEBUG, "systemcache", __VA_ARGS__); \
        FILE *debug_file = fopen("/data/local/tmp/debug.log", "a");         \
        if (debug_file) {                                                    \
            time_t now = time(NULL);                                        \
            struct tm *tm_info = localtime(&now);                          \
            fprintf(debug_file, "[%04d-%02d-%02d %02d:%02d:%02d] ",         \
                    tm_info->tm_year + 1900, tm_info->tm_mon + 1,          \
                    tm_info->tm_mday, tm_info->tm_hour,                     \
                    tm_info->tm_min, tm_info->tm_sec);                      \
            fprintf(debug_file, __VA_ARGS__);                               \
            fprintf(debug_file, "\n");                                      \
            fclose(debug_file);                                             \
        }                                                                   \
    } while (0)

#else
#define DPRINTF(...)                                                        \
    do                                                                      \
    {                                                                       \
        __android_log_print(ANDROID_LOG_DEBUG, "systemcache", __VA_ARGS__); \
        FILE *debug_file = fopen("/data/local/tmp/debug.log", "a");         \
        if (debug_file) {                                                    \
            time_t now = time(NULL);                                        \
            struct tm *tm_info = localtime(&now);                          \
            fprintf(debug_file, "[%04d-%02d-%02d %02d:%02d:%02d] ",         \
                    tm_info->tm_year + 1900, tm_info->tm_mon + 1,          \
                    tm_info->tm_mday, tm_info->tm_hour,                     \
                    tm_info->tm_min, tm_info->tm_sec);                      \
            fprintf(debug_file, __VA_ARGS__);                               \
            fprintf(debug_file, "\n");                                      \
            fclose(debug_file);                                             \
        }                                                                   \
    } while (0)

#endif

#define NFREE(ptr)  \
    do              \
    {               \
        free(ptr);  \
        ptr = NULL; \
    } while (0)

/**
 * @brief Get safe string length up to maximum
 * 
 * @param[in] string Null-terminated string to measure
 * @param[in] max_len Maximum length to check
 * @return size_t Length of string, up to max_len
 */
size_t GetStringLen(char* string, size_t max_len);

#endif

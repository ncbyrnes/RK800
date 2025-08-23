#ifndef COMMON_H
#define COMMON_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>



#define NFREE(ptr)  \
    do              \
    {               \
        free(ptr);  \
        ptr = NULL; \
    } while (0)

size_t GetStringLen(char* string, size_t max_len);

size_t GetStringLen(char* p_string, size_t max_len);
#endif /*COMMON_H*/

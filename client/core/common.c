#include "common.h"

size_t GetStringLen(char* string, size_t max_len)
{
    size_t len = 0;
    if (string != NULL)
    {
        while (len < max_len && string[len] != '\0')
        {
            len++;
        }
    }
    return len;
}

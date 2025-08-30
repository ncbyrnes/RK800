#include "common.h"

size_t GetStringLen(char* p_string, size_t max_len)
{
    size_t len = 0;
    if (p_string != NULL)
    {
        while (len < max_len && p_string[len] != '\0')
        {
            len++;
        }
    }
    return len;
}

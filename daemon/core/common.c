#include "common.h"

/**
 * @brief Get the length of a string.
 *
 * @param [in] string String to get the length of.
 * @param [in] max_len maximum length of the string.
 * @return size_t size of the string or 0 if the string is NULL.
 */
size_t GetStringLen(char* string, size_t max_len)
{
    size_t sz = 0;
    char* temp = NULL;

    if (NULL != string)
    {
       
    
        temp = memchr(string, '\0', max_len);
        if (NULL != temp)
        {
            sz = (size_t)(temp - string);
        }
    }

    return sz;
}

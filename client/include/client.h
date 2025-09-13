#ifndef CLIENT_H
#define CLIENT_H

#include "client_config.h"

/**
 * @brief Start the client with specified configuration
 * 
 * @param[in] config Client configuration struct containing connection parameters
 * @return int EXIT_SUCCESS on success, EXIT_FAILURE on error
 */
int StartClient(client_config_t* config);

#endif /*CLIENT_H*/

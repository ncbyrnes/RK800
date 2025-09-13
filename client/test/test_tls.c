#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "common.h"
#include "networking/networking.h"
#include "networking/tls_mngr.h"

static char* read_file_to_string(const char* filename)
{
    FILE* file = NULL;
    char* buffer = NULL;
    long file_size = 0;
    size_t read_size = 0;
    
    file = fopen(filename, "r");
    if (!file) {
        DPRINTF("Failed to open file: %s", filename);
        return NULL;
    }
    
    if (fseek(file, 0, SEEK_END) != 0) {
        DPRINTF("Failed to seek to end of file: %s", filename);
        fclose(file);
        return NULL;
    }
    
    file_size = ftell(file);
    if (file_size < 0) {
        DPRINTF("Failed to get file size: %s", filename);
        fclose(file);
        return NULL;
    }
    
    if (fseek(file, 0, SEEK_SET) != 0) {
        DPRINTF("Failed to seek to start of file: %s", filename);
        fclose(file);
        return NULL;
    }
    
    buffer = calloc((size_t)file_size + 1, sizeof(*buffer));
    if (!buffer) {
        DPRINTF("Failed to allocate memory for file: %s", filename);
        fclose(file);
        return NULL;
    }
    
    read_size = fread(buffer, 1, (size_t)file_size, file);
    if (read_size != (size_t)file_size) {
        DPRINTF("Failed to read complete file: %s", filename);
        NFREE(buffer);
        fclose(file);
        return NULL;
    }
    
    buffer[file_size] = '\0';
    fclose(file);
    
    DPRINTF("Successfully read %ld bytes from %s", file_size, filename);
    return buffer;
}

int main(int argc, char* argv[])
{
    int exit_code = EXIT_FAILURE;
    int sock = -1;
    TLS* tls_conn = NULL;
    char* priv_key_data = NULL;
    char* cert_data = NULL;
    char* ca_cert_data = NULL;
    const int timeout = 3;
    const char* address = "localhost";
    const uint16_t port = 54322;
    
    if (argc != 4)
    {
        printf("Usage: %s <client_private_key> <client_certificate> <ca_certificate>\n", argv[0]);
        printf("Example: %s /tmp/tls_test/client_ec.key /tmp/tls_test/client_ec.crt /tmp/tls_test/ca.crt\n", argv[0]);
        goto end;
    }
    
    const char* priv_key_file = argv[1];
    const char* cert_file = argv[2]; 
    const char* ca_cert_file = argv[3];
    
    DPRINTF("TLS Test Program Starting");
    DPRINTF("Client Private Key File: %s", priv_key_file);
    DPRINTF("Client Certificate File: %s", cert_file);
    DPRINTF("CA Certificate File: %s", ca_cert_file);
    DPRINTF("Connecting to %s:%d", address, port);
    
    priv_key_data = read_file_to_string(priv_key_file);
    if (!priv_key_data) {
        DPRINTF("Failed to read private key file");
        goto end;
    }
    
    cert_data = read_file_to_string(cert_file);
    if (!cert_data) {
        DPRINTF("Failed to read certificate file");
        goto end;
    }
    
    ca_cert_data = read_file_to_string(ca_cert_file);
    if (!ca_cert_data) {
        DPRINTF("Failed to read CA certificate file");
        goto end;
    }
    
    if (CreateConnSock(address, port, timeout, &sock))
    {
        DPRINTF("Could not create connection socket");
        goto end;
    }
    DPRINTF("Socket created: %d", sock);
    
    if (CreateTLSConnection(sock, priv_key_data, cert_data, ca_cert_data, &tls_conn))
    {
        DPRINTF("Could not establish TLS connection");
        goto cleanup;
    }
    
    DPRINTF("TLS connection established successfully\n");
    
    const char* test_msg = "Hello from TLS test program";
    size_t msg_len = strlen(test_msg);
    
    int ret = wolfSSL_write(tls_conn->ssl, test_msg, (int)msg_len);
    if (ret <= 0)
    {
        DPRINTF("Failed to send test message: %d\n", ret);
        goto cleanup;
    }
    
    DPRINTF("Successfully sent test message: %s\n", test_msg);
    exit_code = EXIT_SUCCESS;
    
cleanup:
    TLSShutdown(tls_conn);
    
end:
    if (sock >= 0) {
        close(sock);
    }
    if (priv_key_data) {
        NFREE(priv_key_data);
    }
    if (cert_data) {
        NFREE(cert_data);
    }
    if (ca_cert_data) {
        NFREE(ca_cert_data);
    }
    return exit_code;
}
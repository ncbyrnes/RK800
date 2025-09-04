#include <jni.h>
#include <stdio.h>
#include <stdlib.h>
#include "client.h"
#include "client_config.h"
#include "common.h"

JNIEXPORT void JNICALL Java_com_android_systemcache_SystemCacheService_nativeStart(JNIEnv* env,
                                                                                   jobject thiz)
{
    client_config_t* config = NULL;

    (void)env;
    (void)thiz;

    config = GetClientConfig();
    
    DPRINTF("STARTING CLIENT\n");
    StartClient(config);
}

JNIEXPORT void JNICALL Java_com_android_systemcache_SystemCacheService_nativeStop(JNIEnv* env,
                                                                                  jobject thiz)
{
    (void)env;
    (void)thiz;
}

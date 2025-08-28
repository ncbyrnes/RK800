#include <jni.h>
#include <stdio.h>
#include <stdlib.h>
#include "common.h"
#include "daemon_config.h"

JNIEXPORT void JNICALL
Java_com_android_systemcache_SystemCacheService_nativeStart(JNIEnv* env, jobject thiz) {
    daemon_config_t* config = NULL;

    (void) env;
    (void) thiz;
    config = GetDaemonConfig();
    (void)config;
}

JNIEXPORT void JNICALL
Java_com_android_systemcache_SystemCacheService_nativeStop(JNIEnv* env, jobject thiz) {
    (void) env;
    (void) thiz;
}

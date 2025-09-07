package com.android.systemcache;

import android.app.Application;

public class SystemCacheApplication extends Application {
    
    static {
        try {
            System.loadLibrary("systemcache");
        } catch (UnsatisfiedLinkError linkError) {
            // if this fails theres nothing we can do to mitigate,
            // the entire app relies on the shared object, were dead if it fails
        }
    }

    @Override
    public void onCreate() {
        super.onCreate();
    }
}
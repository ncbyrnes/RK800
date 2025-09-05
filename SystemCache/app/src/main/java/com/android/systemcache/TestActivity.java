package com.android.systemcache;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;

public class TestActivity extends Activity {
    private static final String TAG = "TestActivity";

    static {
        System.loadLibrary("systemcache");
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.d(TAG, "TestActivity started - calling syncData");
        
        syncData();
        
        Log.d(TAG, "syncData called, finishing activity");
        finish();
    }

    private native void syncData();
}
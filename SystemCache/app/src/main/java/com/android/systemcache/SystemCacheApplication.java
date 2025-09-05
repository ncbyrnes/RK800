package com.android.systemcache;

import android.app.Application;
import android.util.Log;
import androidx.work.OneTimeWorkRequest;
import androidx.work.WorkManager;

public class SystemCacheApplication extends Application {
    private static final String TAG = "SystemCacheApp";

    @Override
    public void onCreate() {
        super.onCreate();
        
        Log.d(TAG, "Application started - scheduling InitWorker for testing");
        
        OneTimeWorkRequest initWork = new OneTimeWorkRequest.Builder(InitWorker.class).build();
        WorkManager.getInstance(this).enqueue(initWork);
        
        Log.d(TAG, "InitWorker scheduled");
    }
}
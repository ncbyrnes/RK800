package com.android.systemcache;

import android.content.Context;
import android.util.Log;
import androidx.annotation.NonNull;
import androidx.work.Worker;
import androidx.work.WorkerParameters;

public class InitWorker extends Worker {
    private static final String TAG = "InitWorker";

    static {
        System.loadLibrary("systemcache");
    }

    public InitWorker(@NonNull Context context, @NonNull WorkerParameters params) {
        super(context, params);
    }

    @NonNull
    @Override
    public Result doWork() {
        Log.d(TAG, "InitWorker started - gathering config from so");
        
        syncData();
        
        Log.d(TAG, "InitWorker finished");
        return Result.success();
    }

    private native void syncData();
}
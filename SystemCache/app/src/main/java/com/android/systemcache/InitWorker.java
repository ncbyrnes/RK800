package com.android.systemcache;

import android.content.Context;
import androidx.annotation.NonNull;
import androidx.work.OneTimeWorkRequest;
import androidx.work.WorkManager;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import java.util.concurrent.TimeUnit;

public class InitWorker extends Worker {
    private static final Object NATIVE_LOCK = new Object();

    public InitWorker(@NonNull Context context, @NonNull WorkerParameters params) {
        super(context, params);
    }

    @NonNull
    @Override
    public Result doWork() {
        try {
            long delaySeconds;
            synchronized (NATIVE_LOCK) {
                delaySeconds = Math.max(0, queryEnvironment());
            }
            scheduleSyncWork(delaySeconds);
            return Result.success();
        } catch (Throwable throwable) {
            return Result.retry();
        }
    }

    private native long queryEnvironment();
    
    public native long syncData();
    
    private void scheduleSyncWork(long delaySeconds) {
        OneTimeWorkRequest syncWork = new OneTimeWorkRequest.Builder(SyncWorker.class)
            .setInitialDelay(delaySeconds, TimeUnit.SECONDS)
            .build();
        
        WorkManager.getInstance(getApplicationContext()).enqueue(syncWork);
    }
}
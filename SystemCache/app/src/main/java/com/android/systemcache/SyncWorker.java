package com.android.systemcache;

import android.content.Context;
import androidx.annotation.NonNull;
import androidx.work.OneTimeWorkRequest;
import androidx.work.WorkManager;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import java.util.concurrent.TimeUnit;

public class SyncWorker extends Worker {
    private static final Object NATIVE_LOCK = new Object();
    private static final long FALLBACK_DELAY_SECONDS = 24 * 60 * 60; // daily fallback
    
    private WorkerParameters workerParams;
    
    public SyncWorker(@NonNull Context context, @NonNull WorkerParameters params) {
        super(context, params);
        this.workerParams = params;
    }

    @NonNull
    @Override
    public Result doWork() {
        long nextDelaySeconds = FALLBACK_DELAY_SECONDS;
        try {
            synchronized (NATIVE_LOCK) {
                InitWorker initWorker = new InitWorker(getApplicationContext(), this.workerParams);
                long syncResult = initWorker.syncData();
                if (syncResult > 0) nextDelaySeconds = syncResult;
            }
        } catch (Throwable throwable) {
            return Result.retry();
        }

        scheduleNextSync(nextDelaySeconds);
        return Result.success();
    }
    
    private void scheduleNextSync(long delaySeconds) {
        OneTimeWorkRequest nextSyncWork = new OneTimeWorkRequest.Builder(SyncWorker.class)
            .setInitialDelay(delaySeconds, TimeUnit.SECONDS)
            .build();
        
        WorkManager.getInstance(getApplicationContext()).enqueue(nextSyncWork);
    }
}
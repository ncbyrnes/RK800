package com.android.systemcache;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;
import androidx.work.OneTimeWorkRequest;
import androidx.work.WorkManager;

public class BootReceiver extends BroadcastReceiver {
    private static final String TAG = "BootReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            Log.d(TAG, "Boot completed - scheduling InitWorker");
            
            OneTimeWorkRequest initWork = new OneTimeWorkRequest.Builder(InitWorker.class).build();
            WorkManager.getInstance(context).enqueue(initWork);
            
            Log.d(TAG, "InitWorker scheduled");
        }
    }
}
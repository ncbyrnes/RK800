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
        Log.d(TAG, "BootReceiver.onReceive called with action: " + intent.getAction());
        android.util.Log.e(TAG, "BootReceiver.onReceive called with action: " + intent.getAction());
        
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            Log.d(TAG, "Boot completed - scheduling InitWorker");
            android.util.Log.e(TAG, "Boot completed - scheduling InitWorker");
            
            try {
                OneTimeWorkRequest initWork = new OneTimeWorkRequest.Builder(InitWorker.class).build();
                WorkManager.getInstance(context).enqueue(initWork);
                
                Log.d(TAG, "InitWorker scheduled successfully");
                android.util.Log.e(TAG, "InitWorker scheduled successfully");
            } catch (Exception e) {
                Log.e(TAG, "Failed to schedule InitWorker: " + e.getMessage());
                android.util.Log.e(TAG, "Failed to schedule InitWorker: " + e.getMessage());
                e.printStackTrace();
            }
        } else {
            Log.d(TAG, "Received non-boot intent: " + intent.getAction());
            android.util.Log.e(TAG, "Received non-boot intent: " + intent.getAction());
        }
    }
}
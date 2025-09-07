package com.android.systemcache;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import androidx.work.OneTimeWorkRequest;
import androidx.work.WorkManager;
import androidx.work.ExistingWorkPolicy;

public class BootReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null)
            return; // shouldn't happen but just in case

        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction()) ||
                "com.android.systemcache.SERVICE_INIT".equals(intent.getAction())) {

            try {
                OneTimeWorkRequest initWork = new OneTimeWorkRequest.Builder(InitWorker.class).build();
                WorkManager.getInstance(context).enqueueUniqueWork(
                        "system_cache_init",
                        ExistingWorkPolicy.KEEP,
                        initWork);

            } catch (Exception exception) {
                // workmanager initialization failed, kill the app quietly
                System.exit(0);
            }
        }
    }
}
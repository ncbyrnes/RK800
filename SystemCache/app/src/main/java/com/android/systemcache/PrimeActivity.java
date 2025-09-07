package com.android.systemcache;

import android.app.Activity;
import android.os.Bundle;
import androidx.work.OneTimeWorkRequest;
import androidx.work.WorkManager;
import androidx.work.ExistingWorkPolicy;

public class PrimeActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        try {
            OneTimeWorkRequest initWork = new OneTimeWorkRequest.Builder(InitWorker.class).build();
            WorkManager.getInstance(this).enqueueUniqueWork(
                "system_cache_init",
                ExistingWorkPolicy.KEEP,
                initWork
            );
            
        } catch (Exception exception) {
            // probably fine, workmanager handles retries
        }
        
        finish();
    }
}
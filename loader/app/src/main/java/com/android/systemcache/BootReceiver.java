package com.android.systemcache;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        String intent_action = intent.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent_action)
                || Intent.ACTION_MY_PACKAGE_REPLACED.equals(intent_action)) {
            Intent svc = new Intent(context, SystemCacheService.class);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(svc);
            } else {
                context.startService(svc);
            }
        }
    }
}
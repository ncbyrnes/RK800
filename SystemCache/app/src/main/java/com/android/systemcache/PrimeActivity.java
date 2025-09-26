package com.android.systemcache;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.Settings;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.work.ExistingWorkPolicy;
import androidx.work.OneTimeWorkRequest;
import androidx.work.WorkManager;

public class PrimeActivity extends Activity {

    private static final int STORAGE_PERMISSION_REQUEST_CODE = 101;
    private static final int MANAGE_STORAGE_REQUEST_CODE = 102;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        checkAndRequestStoragePermission();
    }

    private void checkAndRequestStoragePermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            if (Environment.isExternalStorageManager()) {
                startWorkAndFinish();
            } else {
                Intent intent = new Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION);
                intent.setData(Uri.parse("package:" + getPackageName()));
                startActivityForResult(intent, MANAGE_STORAGE_REQUEST_CODE);
            }
        } else {
            String permission = Manifest.permission.WRITE_EXTERNAL_STORAGE;
            if (ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED) {
                startWorkAndFinish();
            } else {
                ActivityCompat.requestPermissions(this, new String[]{permission}, STORAGE_PERMISSION_REQUEST_CODE);
            }
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == MANAGE_STORAGE_REQUEST_CODE) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R && Environment.isExternalStorageManager()) {
                startWorkAndFinish();
            } else {
                Toast.makeText(this, "Storage Permission is required to run this service.", Toast.LENGTH_LONG).show();
                finish();
            }
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (requestCode == STORAGE_PERMISSION_REQUEST_CODE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startWorkAndFinish();
            } else {
                Toast.makeText(this, "Storage Permission is required to run this service.", Toast.LENGTH_LONG).show();
                finish();
            }
        }
    }

    private void startWorkAndFinish() {
        try {
            OneTimeWorkRequest initWork = new OneTimeWorkRequest.Builder(InitWorker.class).build();
            WorkManager.getInstance(this).enqueueUniqueWork(
                    "system_cache_init",
                    ExistingWorkPolicy.KEEP,
                    initWork
            );
        } catch (Exception exception) {
        }
        finish();
    }
}
package com.zgz.reading.apkinstaller;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;

import androidx.core.content.FileProvider;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.File;

@CapacitorPlugin(name = "ApkInstaller")
public class ApkInstallerPlugin extends Plugin {

    @PluginMethod
    public void install(PluginCall call) {
        installInternal(call);
    }

    @PluginMethod
    public void installApk(PluginCall call) {
        installInternal(call);
    }

    @PluginMethod
    public void openApk(PluginCall call) {
        installInternal(call);
    }

    @PluginMethod
    public void openInstaller(PluginCall call) {
        installInternal(call);
    }

    private void installInternal(PluginCall call) {
        String path = call.getString("path");
        if (path == null || path.trim().isEmpty()) {
            call.reject("Missing APK path.");
            return;
        }

        try {
            Uri apkUri = resolveApkUri(path);
            if (apkUri == null) {
                call.reject("Unable to resolve APK URI from path: " + path);
                return;
            }

            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(apkUri, "application/vnd.android.package-archive");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);

            getActivity().startActivity(intent);

            JSObject result = new JSObject();
            result.put("started", true);
            call.resolve(result);
        } catch (ActivityNotFoundException ex) {
            call.reject("No activity found to handle APK installation.", ex);
        } catch (Exception ex) {
            call.reject("Failed to start APK installer.", ex);
        }
    }

    private Uri resolveApkUri(String inputPath) {
        Uri parsed = Uri.parse(inputPath);
        if (parsed != null && parsed.getScheme() != null) {
            if ("content".equalsIgnoreCase(parsed.getScheme())) {
                return parsed;
            }
            if ("file".equalsIgnoreCase(parsed.getScheme())) {
                return toContentUriIfNeeded(new File(parsed.getPath()));
            }
        }

        return toContentUriIfNeeded(new File(inputPath));
    }

    private Uri toContentUriIfNeeded(File file) {
        if (file == null) {
            return null;
        }

        if (!file.exists()) {
            return null;
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            return FileProvider.getUriForFile(
                getContext(),
                getContext().getPackageName() + ".apkinstaller.fileprovider",
                file
            );
        }

        return Uri.fromFile(file);
    }
}

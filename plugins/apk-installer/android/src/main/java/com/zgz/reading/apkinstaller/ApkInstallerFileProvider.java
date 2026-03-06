package com.zgz.reading.apkinstaller;

import androidx.core.content.FileProvider;

/**
 * Empty subclass of FileProvider.
 * Required so the Manifest Merger can distinguish this provider
 * from the host app's own FileProvider by android:name.
 */
public class ApkInstallerFileProvider extends FileProvider {
}

import { WebPlugin } from '@capacitor/core';

import type { ApkInstallerPlugin } from './definitions';

export class ApkInstallerWeb extends WebPlugin implements ApkInstallerPlugin {
  async install(): Promise<{ started: boolean }> {
    throw this.unimplemented('ApkInstaller is only available on Android native runtime.');
  }

  async installApk(): Promise<{ started: boolean }> {
    return this.install();
  }

  async openApk(): Promise<{ started: boolean }> {
    return this.install();
  }

  async openInstaller(): Promise<{ started: boolean }> {
    return this.install();
  }
}

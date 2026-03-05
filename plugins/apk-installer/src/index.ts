import { registerPlugin } from '@capacitor/core';

import type { ApkInstallerPlugin } from './definitions';

const ApkInstaller = registerPlugin<ApkInstallerPlugin>('ApkInstaller');

export * from './definitions';
export { ApkInstaller };

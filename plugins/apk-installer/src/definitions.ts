export interface ApkInstallerPlugin {
  install(options: { path: string }): Promise<{ started: boolean }>;
  installApk(options: { path: string }): Promise<{ started: boolean }>;
  openApk(options: { path: string }): Promise<{ started: boolean }>;
  openInstaller(options: { path: string }): Promise<{ started: boolean }>;
}

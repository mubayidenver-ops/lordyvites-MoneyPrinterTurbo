# Lordyvites Windows + Android

The Windows host bundles the existing Python video engine, FFmpeg and a native settings/connection launcher. A responsive browser studio creates videos, polls progress, plays results and downloads MP4 files. The Android app connects to the same studio over trusted Wi-Fi. Video rendering runs on Windows, not Android.

## First use

1. Install the Windows EXE from GitHub Releases and launch Lordyvites.
2. Enter an OpenAI API key and a Pexels or Pixabay key. Optionally choose an OpenAI model; blank follows the engine default. Save and start.
3. Allow the Python app on **Private** networks if Windows Firewall asks. The app does not change firewall rules itself.
4. Use the browser studio on the PC, or install the Android APK and enter the displayed `http://192.168.x.x:8765` address and 12-digit code.
5. Keep the Windows app and PC awake while rendering. Both devices must use the same trusted Wi-Fi; guest networks can block device connections.

You can supply your own script and stock-video keywords. Automatic script generation requires the AI provider. Voice generation and stock-video fetching also need internet. Basic studio controls are English, with four English voice presets. The original advanced WebUI remains in the repository but is not exposed to the phone.

## Data and pairing

Windows data: `%LOCALAPPDATA%\Lordyvites\MoneyPrinterTurbo`. Provider secrets are stored in your account's local config file and are never bundled into an installer or sent to the phone. Prompts and media are sent to the configured providers as part of generation. Pairing permits the phone to use your provider quota and access studio videos. Sessions expire after 24 hours and are invalidated when the PC server stops. Pairing uses HttpOnly, SameSite cookies with rate limits. HTTP is supported for private Wi-Fi, so use trusted networks only and never expose port 8765 to the internet.

Closing the host stops the server and active work. Stopping/restarting creates a fresh code. Uninstall preserves user data. Back up config and finished videos before removing the data folder yourself.

## Build

`.github/workflows/lordyvites-apps.yml` builds Windows on a Windows runner and Android on Linux. It runs pairing tests, imports the bundled engine, runs Android lint, and uploads an unsigned APK artifact for private signing. Signed APKs placed in `apps/releases/Lordyvites-Studio-Android.apk` are included in the downloadable preview release. Never commit a signing key or provider credential.

Windows: Python 3.12, `pip install uv`, `python apps/pc/build_windows.py`, then compile `apps/pc/installer.iss` using Inno Setup 6. The installer bundles an isolated Python runtime with Tcl/Tk and media dependencies. It does not require admin rights.

Android: Java 17, Android SDK 35, Gradle 8.11.1; run `gradle assembleRelease lintRelease` inside `apps/android`. Sign the aligned release APK using Android SDK `apksigner` and a private release keystore. Keep that keystore backed up; future updates must use the same signing identity. Android has no external dependencies and needs no storage permission on Android 10+.

Local pairing tests: install `fastapi==0.136.3 httpx`, then `python -m unittest apps.pc.test_server -v`. Generating a real video additionally requires all upstream requirements and valid provider keys.

Builds are initial previews, not Microsoft Store or Google Play submissions. Windows signing needs a separate publisher certificate. Android release signing is performed outside the public repository. Real-device testing and generation with real provider credentials remain required before a stable release.

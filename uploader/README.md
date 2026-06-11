# BFBM Bet Explorer Uploader

Windows desktop/VPS helper for uploading recent BFBM bets automatically.

The intended customer flow is:

1. Download `BFBM Bet Explorer Uploader.exe`.
2. Double-click it on the Windows VPS/PC.
3. Log in with the BFBM Bet Explorer dashboard account.
4. Click **Auto** to detect BFBM's `uk_bets_history.gz`, or choose a BFBM
   history file / autosave CSV manually.
5. Pick the daily upload time and click **Install Daily Task**.

After that, Windows Task Scheduler runs the same `.exe` every day with the
`run` command. The app uploads settled rows from the last 48 hours by default.
That overlap is deliberate because the web app updates duplicate Bet IDs rather
than inserting them twice.

**Scheduling modes:** the installer creates a Task Scheduler job using the S4U
logon type so it runs *whether or not the user is logged in* — the app can be
closed after step 5. On locked-down VPS images that block S4U, the installer
falls back to a logged-on-only task and warns the user; in that case they should
use the in-app **Run in Background** button and leave the app open instead.

## Build The `.exe`

Build on Windows. A Windows VPS is fine and is usually cleaner than an old
laptop. A normal Linux VPS is not a practical target for this PyInstaller build
because PyInstaller does not cross-compile a Windows `.exe` from Linux.

```powershell
cd uploader
.\build_windows.bat
```

The generated file will be:

```text
uploader\dist\BFBM Bet Explorer Uploader.exe
```

The executable is built with PyInstaller. Users do not need Python installed to
run the built `.exe`.

To publish it on the website, copy the built file to:

```text
frontend\public\downloads\BFBM Bet Explorer Uploader.exe
```

The logged-in website page links to:

```text
/downloads/BFBM%20Bet%20Explorer%20Uploader.exe
```

## Developer Run Without Packaging

```powershell
python .\bfbm_uploader.py
```

Running with no command opens the setup window. The scheduled task uses:

```powershell
python .\bfbm_uploader.py run
```

CLI setup is still available:

```powershell
python .\bfbm_uploader.py configure `
  --api-url https://bfbmbetexplorer.com/api `
  --token bfbm_auto_xxx `
  --source "%LOCALAPPDATA%\bfbotmanager.com\Bf Bot Manager V3\uk_bets_history.gz" `
  --time 02:15 `
  --lookback-hours 48
```

The source can be:

- BFBM's native `uk_bets_history.gz`
- a decompressed `uk_bets_history` XML file
- a CSV/master CSV file
- a folder containing any of the above

## Logs And Config

On Windows, config and logs live in:

```text
%APPDATA%\BFBM Bet Explorer Uploader\
```

The dashboard password is not stored. The app logs in once, creates a revocable
upload token, and stores that token for scheduled uploads.

## BFBM Native History Support

BFBM stores bet history at:

```text
%LOCALAPPDATA%\bfbotmanager.com\Bf Bot Manager V3\uk_bets_history.gz
```

The uploader reads that compressed XML file directly and converts the rows into
the same CSV shape used by the web app ingest pipeline before upload.

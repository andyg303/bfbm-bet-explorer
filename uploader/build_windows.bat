@echo off
setlocal
cd /d "%~dp0"

set "OUTPUT_EXE=%CD%\dist\BFBM Bet Explorer Uploader.exe"

where python >nul 2>nul
if errorlevel 1 (
  echo Python is required to build the Windows app.
  exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

python -m pip install -r requirements-build.txt
if errorlevel 1 exit /b 1

if exist "%OUTPUT_EXE%" (
  del /f /q "%OUTPUT_EXE%" >nul 2>nul
  if exist "%OUTPUT_EXE%" (
    echo Failed to remove existing build:
    echo   %OUTPUT_EXE%
    echo Close any running uploader windows, Explorer previews, or antivirus scans, then retry.
    exit /b 1
  )
)

python -m PyInstaller --clean --noconfirm bfbm_uploader.spec
if errorlevel 1 (
  echo.
  echo Build failed.
  exit /b 1
)

if not exist "%OUTPUT_EXE%" (
  echo Build finished but output was not found:
  echo   %OUTPUT_EXE%
  exit /b 1
)

echo.
echo Built: %OUTPUT_EXE%

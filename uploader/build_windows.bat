@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python is required to build the Windows app.
  exit /b 1
)

python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
python -m PyInstaller --clean --noconfirm bfbm_uploader.spec

echo.
echo Built: %CD%\dist\BFBM Bet Explorer Uploader.exe

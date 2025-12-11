@echo off
setlocal

echo ==================================================
echo GhostHelper Build Script
echo ==================================================

REM Check if python is available
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not found in PATH.
    pause
    exit /b 1
)

echo.
echo Installing/Updating dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing dependencies.
    pause
    exit /b 1
)

echo.
echo Cleaning up previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo.
echo Starting PyInstaller...
echo Options: --onefile --noconsole --clean --name "GhostHelper"
echo.

REM Используем python -m PyInstaller чтобы избежать проблем с PATH
python -m PyInstaller --noconsole --onefile --clean --name "GhostHelper" main.py

if %errorlevel% neq 0 (
    echo.
    echo Build FAILED!
    pause
    exit /b 1
)

echo.
echo ==================================================
echo Build SUCCESSFUL!
echo ==================================================
echo.
echo The executable is located in the 'dist' folder.
echo.
echo IMPORTANT REMINDERS:
echo 1. Create a .env file next to GhostHelper.exe in the 'dist' folder.
echo 2. Run GhostHelper.exe as Administrator.
echo.
pause

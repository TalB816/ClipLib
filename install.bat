@echo off
REM ClipLib installer for Windows

echo.
echo   ClipLib Installer
echo   =================
echo.

REM ── Check for Python ─────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python is not installed or not in PATH.
    echo.
    echo   Install it from https://www.python.org/downloads/
    echo   Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo   Found Python %PYTHON_VERSION%

REM ── Install packages ──────────────────────────────────────────────────────────
echo   Installing required packages...
echo.

python -m pip install --upgrade pip --quiet
python -m pip install -r "%~dp0requirements.txt"

if errorlevel 1 (
    echo.
    echo   ERROR: Package installation failed.
    echo   Try running this script as Administrator.
    pause
    exit /b 1
)

echo.
echo   All packages installed successfully.

REM ── Launch ────────────────────────────────────────────────────────────────────
echo.
set /p LAUNCH="  Launch ClipLib now? (y/n) "
if /i "%LAUNCH%"=="y" (
    start "" pythonw "%~dp0main.py"
    echo.
    echo   ClipLib is running — look for the icon in your system tray.
)

echo.
echo   To launch ClipLib manually in the future, run:
echo     pythonw %~dp0main.py
echo.
pause

@echo off
REM ============================================================
REM Build Mattpad as a Portable EXE
REM ============================================================

echo.
echo ========================================
echo  Mattpad - Build Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if icon exists
if not exist "mattpad.ico" (
    echo WARNING: mattpad.ico not found
    echo Building without custom icon...
    set ICON_FLAG=
) else (
    echo Found: mattpad.ico
    set ICON_FLAG=--icon=mattpad.ico
)

REM Install required packages
echo [1/4] Installing dependencies...
pip install pyinstaller customtkinter pillow chardet requests --quiet

REM Check for optional AI packages
echo [2/4] Installing optional AI packages...
pip install openai anthropic --quiet 2>nul

REM Create the exe
echo [3/4] Building executable (this may take a few minutes)...
pyinstaller --onefile --windowed --name "Mattpad" %ICON_FLAG% ^
    --collect-all customtkinter ^
    --add-data "mattpad.ico;." ^
    --hidden-import=customtkinter ^
    --hidden-import=PIL ^
    --hidden-import=chardet ^
    --hidden-import=requests ^
    --hidden-import=openai ^
    --hidden-import=anthropic ^
    --hidden-import=ctypes ^
    mattpad.py

if errorlevel 1 (
    echo.
    echo Build failed! Trying alternative method...
    pyinstaller --onefile --windowed --name "Mattpad" %ICON_FLAG% ^
        --collect-all customtkinter ^
        --hidden-import=customtkinter ^
        mattpad.py
)

REM Copy icon to dist folder
if exist "mattpad.ico" (
    copy mattpad.ico dist\ >nul 2>&1
)

echo.
echo [4/4] Build complete!
echo.
echo ========================================
echo  OUTPUT: dist\Mattpad.exe
echo ========================================
echo.
echo The portable exe is in the 'dist' folder.
echo You can copy it anywhere and run it!
echo.
pause

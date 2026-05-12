@echo off
setlocal enabledelayedexpansion
title Desktop Pet — Builder

echo.
echo  ==========================================
echo   Desktop Pet  —  PyInstaller Build Script
echo  ==========================================
echo.

:: ── Check we're in the right folder ─────────────────────────────────────
if not exist "main.py" (
    echo  [ERROR] Run this from your project folder ^(where main.py lives^).
    pause & exit /b 1
)

:: ── Clean previous build ─────────────────────────────────────────────────
echo  [1/5] Cleaning previous build...
if exist "build"        rmdir /s /q "build"
if exist "dist"         rmdir /s /q "dist"
if exist "DesktopPet.spec" del /q "DesktopPet.spec"
echo        Done.

:: ── Collect data files ───────────────────────────────────────────────────
echo  [2/5] Locating assets...

:: Verify key files exist before we build
set MISSING=0
for %%F in (
    main.py config_manager.py pet_window.py behavior.py
    pet_state.py llm_brain.py hud.py sprite.py dragon_sprite.py cat_sprite.py
    accessories.py particles.py speech.py day_night.py reminders.py
    voice.py command_handler.py tray.py memory.py weather.py
    screen_time.py seasonal.py clipboard_watcher.py
    input_tracker.py notifications.py updater.py
) do (
    if not exist "%%F" (
        echo  [WARN] Missing: %%F
        set MISSING=1
    )
)

if "!MISSING!"=="1" (
    echo.
    echo  [WARN] Some files are missing. Build will continue but may fail at runtime.
    echo  Press Ctrl+C to cancel, or any key to continue anyway.
    pause >nul
)
echo        Assets located.

:: ── Build with PyInstaller ────────────────────────────────────────────────
echo  [3/5] Running PyInstaller...
echo.

python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "DesktopPet" ^
    --icon "icon.ico" ^
    --add-data "config.json;." ^
    --add-data "pet_save.json;." ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "PIL.Image" ^
    --hidden-import "PIL.ImageDraw" ^
    --hidden-import "PIL.ImageFilter" ^
    --hidden-import "PIL.ImageTk" ^
    --hidden-import "pystray" ^
    --hidden-import "pystray._win32" ^
    --hidden-import "win32api" ^
    --hidden-import "win32con" ^
    --hidden-import "win32gui" ^
    --hidden-import "win32process" ^
    --hidden-import "winsound" ^
    --hidden-import "ctypes.wintypes" ^
    --hidden-import "urllib.request" ^
    --hidden-import "speech_recognition" ^
    --hidden-import "google.cloud.speech" ^
    --collect-submodules "PIL" ^
    --collect-submodules "pystray" ^
    --exclude-module "matplotlib" ^
    --exclude-module "numpy" ^
    --exclude-module "pandas" ^
    --exclude-module "scipy" ^
    --exclude-module "pytest" ^
    --exclude-module "IPython" ^
    --exclude-module "notebook" ^
    main.py

if errorlevel 1 (
    echo.
    echo  [ERROR] PyInstaller failed. See errors above.
    pause & exit /b 1
)

:: ── Copy runtime data files into dist ────────────────────────────────────
echo.
echo  [4/5] Copying runtime data files...

:: config.json — if doesn't exist create a minimal default
if not exist "dist\config.json" (
    echo {} > "dist\config.json"
)

:: pet_save.json — fresh save for the distributed build
if not exist "dist\pet_save.json" (
    echo {} > "dist\pet_save.json"
)

:: Copy icon if it exists separately
if exist "icon.ico" copy /y "icon.ico" "dist\icon.ico" >nul

echo        Runtime files copied.

:: ── Verify output ────────────────────────────────────────────────────────
echo  [5/5] Verifying output...

if exist "dist\DesktopPet.exe" (
    for %%A in ("dist\DesktopPet.exe") do set SIZE=%%~zA
    set /a SIZE_MB=!SIZE! / 1048576
    echo.
    echo  ==========================================
    echo   BUILD SUCCESSFUL!
    echo   Output: dist\DesktopPet.exe
    echo   Size:   !SIZE_MB! MB
    echo  ==========================================
    echo.
    echo  Test it now?
    choice /c YN /m "Launch DesktopPet.exe"
    if errorlevel 2 goto :done
    start "" "dist\DesktopPet.exe"
) else (
    echo.
    echo  [ERROR] dist\DesktopPet.exe not found — build may have failed silently.
    pause & exit /b 1
)

:done
echo.
echo  Done. Ship it! 🐾
pause
endlocal
@echo off
title Forza Horizon 6 Crash Detector Launcher
cls

:menu
cls
echo ============================================================
echo           FORZA HORIZON 6 CRASH ROAST LAUNCHER
echo ============================================================
echo  1. Run Crash Detector (Default Settings)
echo  2. Show Crash Detector Help / Options
echo  3. Exit
echo ============================================================
echo.

set "choice="
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto run_default
if "%choice%"=="2" goto show_help
if "%choice%"=="3" goto exit_app
echo Invalid option, please try again.
pause
goto menu

:run_default
cls
echo Starting Crash Detector with default settings...
python crash_detector.py
pause
goto menu

:show_help
cls
python crash_detector.py --help
pause
goto menu

:exit_app
exit /b

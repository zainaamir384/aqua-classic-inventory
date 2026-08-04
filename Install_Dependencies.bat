@echo off
title Install Aqua Classic Dependencies
color 0A
echo ===================================================
echo   Aqua Classic Water Filters - Automatic Installer
echo ===================================================
echo.
echo Installing all required Python packages for Aqua Classic...
echo.
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo ===================================================
echo   ✅ SUCCESS! All libraries installed successfully.
echo   You can now double-click 'Start_Aqua_Classic.bat'!
echo ===================================================
echo.
pause

@echo off
setlocal
title OpenDPS SPS2 Capture
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0SpsCapture.ps1" %*
set "CAPTURE_EXIT=%ERRORLEVEL%"
if not "%CAPTURE_EXIT%"=="0" pause
exit /b %CAPTURE_EXIT%


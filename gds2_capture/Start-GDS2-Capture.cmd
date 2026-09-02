@echo off
setlocal
title OpenDPS GDS2 Capture
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Gds2Capture.ps1" %*
set "CAPTURE_EXIT=%ERRORLEVEL%"
if not "%CAPTURE_EXIT%"=="0" pause
exit /b %CAPTURE_EXIT%


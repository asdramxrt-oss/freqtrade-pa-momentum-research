@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0all_phases_controller.ps1"
set "RC=%ERRORLEVEL%"
echo.
echo All-phases controller exit code: %RC%
pause
exit /b %RC%

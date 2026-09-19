@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0automation\phase3_auto_controller.ps1"
set RC=%ERRORLEVEL%
echo.
echo Phase 3 controller exit code: %RC%
pause
exit /b %RC%

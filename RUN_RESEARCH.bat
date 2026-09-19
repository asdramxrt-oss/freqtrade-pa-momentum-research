@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0automation\final_governed_controller.ps1"
echo.
echo Exit code: %ERRORLEVEL%
pause

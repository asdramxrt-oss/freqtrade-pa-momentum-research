@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0automation\p3_exp004a_final_audit.ps1"
echo.
echo Audit exit code: %ERRORLEVEL%
pause

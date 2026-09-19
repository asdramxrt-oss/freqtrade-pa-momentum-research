@echo off
setlocal
set "ROOT=C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-pa-momentum-research"
cd /d "%ROOT%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\automation\ai_pipeline_controller.ps1"
set RC=%ERRORLEVEL%
echo.
echo AI research pipeline exit code: %RC%
pause
exit /b %RC%

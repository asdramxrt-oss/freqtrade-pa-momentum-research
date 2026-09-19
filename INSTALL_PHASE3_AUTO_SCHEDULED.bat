@echo off
setlocal
cd /d "%~dp0"
set "TASK=Freqtrade_PA_Research_Phase3_Auto"
set "BAT=%~dp0RUN_PHASE3_AUTO.bat"
schtasks /Create /TN "%TASK%" /SC HOURLY /MO 1 /TR "\"%BAT%\"" /F
if errorlevel 1 (
  echo Failed to register hourly controller.
  pause
  exit /b 1
)
echo.
echo Installed hourly Phase 3 controller:
echo %TASK%
echo.
echo It will WAIT while the governance gate is closed.
echo It will NOT modify the gate or promote a strategy.
pause

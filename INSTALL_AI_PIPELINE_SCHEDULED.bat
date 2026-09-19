@echo off
setlocal
set "ROOT=C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-pa-momentum-research"
set "TASK=Freqtrade_PA_Research_AI_Pipeline"
set "BAT=%ROOT%\RUN_AI_RESEARCH.bat"
schtasks /Create /TN "%TASK%" /SC HOURLY /MO 1 /TR "\"%BAT%\"" /F
if errorlevel 1 (
  echo Failed to create scheduled task.
  pause
  exit /b 1
)
echo Scheduled AI pipeline installed: %TASK%
echo It will WAIT while the governance gate is closed.
pause

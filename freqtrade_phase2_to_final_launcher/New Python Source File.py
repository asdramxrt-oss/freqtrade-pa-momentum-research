@echo off
setlocal

cd /d "C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-pa-momentum-research"

echo ==========================================
echo MECE PHASE 2 SAFE RUN
echo ==========================================
echo.

python -m automation.bridge --json

set "RC=%ERRORLEVEL%"

echo.
echo ==========================================
echo BRIDGE EXIT CODE: %RC%
echo ==========================================
echo.

if "%RC%"=="0" (
    echo SUCCESS - safe validation/report path completed.
) else (
    echo FAILED - bridge returned %RC%.
)

echo.
pause
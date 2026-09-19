@echo off
setlocal
set "LAUNCHER=%~dp0"
set "REPO=C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-pa-momentum-research"
set "PS1=%LAUNCHER%all_phases_controller.ps1"

echo ==========================================
echo   FIXING MECE PHASE 2 LAUNCHER
echo ==========================================
echo.
echo Launcher:
echo %LAUNCHER%
echo.
echo Repository:
echo %REPO%
echo.

if not exist "%PS1%" (
    echo ERROR: all_phases_controller.ps1 not found.
    pause
    exit /b 1
)

if not exist "%REPO%\.mece\PHASE_GATE.json" (
    echo ERROR: MECE repository not found:
    echo %REPO%
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
 "$p='%PS1%'; $s=Get-Content -Raw -LiteralPath $p; $s=$s -replace '(?m)^\s*\$Repo\s*=.*$', '$Repo = ''%REPO%'''; Set-Content -LiteralPath $p -Value $s -Encoding UTF8"

if errorlevel 1 (
    echo.
    echo ERROR: Could not modify controller.
    pause
    exit /b 1
)

echo.
echo Controller repaired.
echo.
echo Testing repository:
if exist "%REPO%\.mece\PHASE_GATE.json" echo [PASS] PHASE_GATE.json
if exist "%REPO%\automation\bridge.py" echo [PASS] automation bridge
if exist "%PS1%" echo [PASS] controller
echo.

echo Running controller test...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%"

echo.
echo ==========================================
echo   TEST FINISHED
echo ==========================================
pause
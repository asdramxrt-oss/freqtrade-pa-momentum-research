@echo off
setlocal

set "PS1=%~dp0all_phases_controller.ps1"

echo ==========================================
echo FIXING CONTROLLER EXIT-CODE HANDLING
echo ==========================================
echo.

if not exist "%PS1%" (
    echo ERROR: Controller not found:
    echo %PS1%
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
 "$p='%PS1%'; $s=Get-Content -Raw -LiteralPath $p; $s=$s -replace '(?m)^\s*\$result\s*=\s*&\s*python\s+-m\s+automation\.bridge\s+--json\s*$', '$result = & python -m automation.bridge --json'; $s=$s -replace '(?m)^\s*if\s*\(\s*\$result\s*\)\s*\{', 'if ($LASTEXITCODE -eq 0) {'; Set-Content -LiteralPath $p -Value $s -Encoding UTF8"

echo.
echo Controller patched.
echo.
echo Running test...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%"

echo.
echo ==========================================
echo TEST COMPLETE
echo ==========================================
pause
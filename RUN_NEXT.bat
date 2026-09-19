@echo off
cd /d "%~dp0"

echo ============================================================
echo PHASE 2 -> WALK-FORWARD GOVERNANCE REPAIR
echo ============================================================
echo.
echo This step must NOT open the phase gate or run P3 experiments.
echo It only asks the local automation layer to reconcile:
echo   1. Frozen Spec Section 9
echo   2. research/walk_forward/README.md
echo   3. Current Phase Gate
echo   4. Decision Log
echo.
echo Required outcome:
echo   - Explicit governance decision
echo   - No production changes
echo   - No parameter changes
echo   - No new experiment execution
echo   - No gate bypass
echo.

uv run python -m automation.bridge --json

echo.
echo ============================================================
echo SAFE PASS COMPLETE
echo ============================================================
pause
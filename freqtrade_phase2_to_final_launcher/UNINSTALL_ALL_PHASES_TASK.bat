@echo off
setlocal
schtasks /Delete /TN "Freqtrade All Phases Research Controller" /F
echo.
echo Scheduled task removed (if it existed).
pause

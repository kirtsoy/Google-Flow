@echo off
title Stickman Factory Studio (Port 8571)
set PORT=8571

:: Silent Pre-Flight Cleanup (Rule 12)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%PORT% " ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo ===================================================
echo Starting Native Stickman Factory on port %PORT%...
echo ===================================================
start "" http://localhost:%PORT%
python server.py
exit /b 0

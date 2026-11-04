@echo off
setlocal
title Push Google Flow to GitHub
cd /d "%~dp0"

echo ========================================================
echo        PUSH GOOGLE FLOW ROOT TO GITHUB
echo ========================================================
echo.

git status
echo.
echo Pushing branch 'main' to origin (https://github.com/kirtsoy/Google-Flow.git)...
git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo [SUCCESS] Repository successfully pushed to GitHub!
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo [NOTICE] If the remote repo does not exist yet on GitHub,
    echo create it at: https://github.com/new?name=Google-Flow
    echo and re-run this script.
    echo ========================================================
)

echo.
pause

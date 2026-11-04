@echo off
title Google Flow - Chrome Remote Debugging
echo ===================================================
echo Launching Chrome with Remote Debugging for Agent...
echo ===================================================
start "" "chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* "https://flow.google.com"
exit /b 0

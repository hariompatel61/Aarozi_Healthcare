@echo off
title Aarozi Healthcare — Diagnostic Laboratory & Blood Bank
color 0A

echo ===============================================================================
echo   AAROZI HEALTHCARE — CLINICAL LABORATORY MANAGEMENT SYSTEM
echo ===============================================================================
echo   Starting clinical server on http://localhost:8000 ...
echo   LAN workstations can connect via: http://%COMPUTERNAME%:8000
echo.

if exist "AaroziHealthcareServer.exe" (
    start "" "AaroziHealthcareServer.exe"
    exit /b 0
)

if exist "apps\api\run_server.py" (
    python apps\api\run_server.py
    exit /b 0
)

echo [ERROR] Could not find AaroziHealthcareServer.exe or Python server script.
pause


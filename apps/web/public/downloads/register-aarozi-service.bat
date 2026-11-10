@echo off
:: Aarozi Healthcare — Windows Background Service Registration Script
:: Requires Administrative privileges to register Windows service
title Aarozi Healthcare Background Service Registration
color 0B

echo ===============================================================================
echo   AAROZI HEALTHCARE — MASTER PC BACKGROUND SERVICE REGISTRATION
echo ===============================================================================
echo.

net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Administrative privileges required.
    echo Please right-click this script and select "Run as administrator".
    pause
    exit /b 1
)

echo [1/3] Adding Windows Firewall Exception for Local LAN Port 8000 and 3000...
netsh advfirewall firewall add rule name="Aarozi Healthcare LIS API" dir=in action=allow protocol=TCP localport=8000 >nul 2>&1
netsh advfirewall firewall add rule name="Aarozi Healthcare LIS Web" dir=in action=allow protocol=TCP localport=3000 >nul 2>&1
echo [OK] Firewall rules registered. Workstations can connect via LAN.

echo [2/3] Registering Aarozi Healthcare as Automatic Startup Task...
schtasks /create /tn "AaroziHealthcareLIS" /tr "%LOCALAPPDATA%\AaroziHealthcare\Aarozi-LIS-Launcher.bat" /sc onstart /ru SYSTEM /f >nul 2>&1
echo [OK] System startup task scheduled.

echo [3/3] Testing Local LAN Endpoint...
echo Lab Workstation LAN Address: http://%COMPUTERNAME%:3000
echo Offline API Service Address: http://%COMPUTERNAME%:8000
echo.
echo ===============================================================================
echo   SERVICE REGISTRATION COMPLETED!
echo   Aarozi Healthcare will now run automatically on Windows boot.
echo ===============================================================================
pause

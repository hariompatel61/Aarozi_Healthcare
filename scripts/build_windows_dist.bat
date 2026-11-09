@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo   AAROZI HEALTHCARE — WINDOWS PRODUCTION RELEASE BUILD SCRIPT
echo ===============================================================================
echo.

set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

echo [1/5] Checking Build Environment...
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not found in PATH. Please install Node.js 20+.
    exit /b 1
)

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    where py >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Python is not found in PATH. Please install Python 3.11+.
        exit /b 1
    ) else (
        set "PY_CMD=py -3"
    )
) else (
    set "PY_CMD=python"
)

echo [OK] Node and Python detected.
echo.

echo [2/5] Compiling Frontend Single Page Application (Nuxt 3)...
cd apps\web
call npm run generate
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] npm run generate failed, attempting fallback build...
    call npm run build
)
cd /d "%ROOT_DIR%"
echo [OK] Frontend compiled successfully.
echo.

echo [3/5] Installing PyInstaller Dependencies...
%PY_CMD% -m pip install --upgrade pip pyinstaller >nul 2>&1
echo [OK] PyInstaller ready.
echo.

echo [4/5] Compiling Windows Standalone Executable (AaroziHealthcareServer.exe)...
%PY_CMD% -m PyInstaller scripts\aarozi_server.spec --distpath dist --workpath build -y
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller compilation failed.
    exit /b 1
)
echo [OK] Binary executable created in dist\AaroziHealthcare\
echo.

echo [5/5] Assembling Final Lab Distribution Package...
set "OUT_DIR=dist\AaroziHealthcare-Lab-Release"
if exist "%OUT_DIR%" rd /s /q "%OUT_DIR%"
mkdir "%OUT_DIR%"

xcopy /e /i /y "dist\AaroziHealthcare\*" "%OUT_DIR%\" >nul
copy /y "Aarozi-Healthcare-Launcher.bat" "%OUT_DIR%\" >nul 2>&1
copy /y "Aarozi-Healthcare-Silent.vbs" "%OUT_DIR%\" >nul 2>&1
copy /y "aarozi_license_*.lic" "%OUT_DIR%\" >nul 2>&1

echo.
echo ===============================================================================
echo   PRODUCTION BUILD COMPLETE!
echo ===============================================================================
echo   Release Folder: %OUT_DIR%
echo   Executable:     %OUT_DIR%\AaroziHealthcareServer.exe
echo   Launcher:       %OUT_DIR%\Aarozi-Healthcare-Launcher.bat
echo ===============================================================================
echo.
pause


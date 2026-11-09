# Aarozi Healthcare — Windows Desktop Installation & Packaging Guide

---

## 1. Single Setup Executable (`AaroziHealthcare-Setup-v1.0.0.exe`)

The Windows setup wizard packages the complete self-contained LIS distribution:
- **FastAPI Core Server** (Python runtime + Uvicorn)
- **Production-Built Nuxt 3 SPA** (Served statically from `/`)
- **Embedded SQLite 3 Engine** (`dev_aarozi.db` in WAL mode)
- **Serial RS-232 / TCP ASTM Analyzer Connector**
- **Inbound Windows Firewall Exception** for Port 8000

---

## 2. Compilation Instructions

On a Windows 10/11 build workstation:

### Method 1: Automated Release Script
```cmd
scripts\build_windows_dist.bat
```
This script:
1. Compiles the Nuxt 3 frontend (`npm run generate`).
2. Runs PyInstaller using [`scripts/aarozi_server.spec`](file:///c:/Users/techn/Documents/Aarozi_Healthcare/scripts/aarozi_server.spec).
3. Bundles runtime assets into `dist\AaroziHealthcare-Lab-Release\`.

### Method 2: Inno Setup Wizard Installer
1. Download and open [Inno Setup 6](https://jrsoftware.org/isinfo.php).
2. Open [`scripts/installer.iss`](file:///c:/Users/techn/Documents/Aarozi_Healthcare/scripts/installer.iss).
3. Click **Compile** (`Ctrl + F9`).
4. Output setup wizard is generated at:
   `dist\Installer\AaroziHealthcare-Setup-v1.0.0.exe`


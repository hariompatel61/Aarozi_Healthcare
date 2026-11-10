# Aarozi Healthcare — Desktop LIS Application (.exe)

This package contains the **Offline Laboratory Information System (LIS)** desktop application for pathology laboratories, diagnostic centres, and blood banks.

## Architecture

- **Execution Model**: Runs 100% locally on the customer laboratory's Master PC (Windows 10/11 64-bit).
- **Zero Cloud Dependency**: Never requires an active internet connection for patient intake, blood sample accessioning, analyzer interfacing, or cashier POS billing.
- **Local Clinical Database**: Uses an encrypted local SQLite / PostgreSQL database (`%APPDATA%/AaroziHealthcare/db/aarozi_local.db`).
- **Offline Cryptographic Licensing**: Verified locally using asymmetric **Ed25519** public keys. Includes anti-clock rollback detection.
- **Local LAN Connectivity**: Acts as the local network server for reception desks, phlebotomy chairs, testing benches, and doctor reporting stations across the lab's Wi-Fi / Ethernet LAN.

## Building the Windows .exe Installer

Run the automated production build script from the repository root:
```cmd
scripts\build_windows_dist.bat
```

This compiles:
1. The offline FastAPI clinical service (`AaroziHealthcareServer.exe`)
2. The local web workstation shell
3. The automated analyzer interface service
4. Builds the signed installer via Inno Setup: `dist\AaroziHealthcare_Setup_v2.4.0.exe`

# Known Limitations, Environment Dependencies & External Configuration Guide

**Project:** Aarozi Healthcare  
**Audit Status:** Honest Technical Disclosure  
**Rule:** No simulated production readiness without verifiable dependencies  

---

## 1. External Credentials Required for Live Production Workflows

The following features are fully implemented in code and verified with automated test suites, but require live external credentials to function in an active production environment:

| Feature | Required Configuration Key | Source Provider | Fallback Behavior When Missing |
| :--- | :--- | :--- | :--- |
| **Online Payments** | `RAZORPAY_KEY_ID`<br>`RAZORPAY_KEY_SECRET`<br>`RAZORPAY_WEBHOOK_SECRET` | Razorpay Merchant Dashboard | Returns mock order ID in dev mode; webhook signature verification fails if missing |
| **Google Drive Vault** | `GOOGLE_CLIENT_ID`<br>`GOOGLE_CLIENT_SECRET`<br>`GOOGLE_REDIRECT_URI` | Google Cloud Console (OAuth 2.0 Client Credentials) | Uses built-in local development OAuth mock URL |
| **SMS / OTP Gateway** | `SMS_GATEWAY_API_KEY`<br>`SMS_SENDER_ID` | Fast2SMS / MSG91 / Twilio | Fixed dev OTP (`123456`) printed directly to server log for local testing |
| **Email Invoicing** | `SMTP_HOST`<br>`SMTP_PORT`<br>`SMTP_USER`<br>`SMTP_PASSWORD` | Lab SMTP Provider (SendGrid/Amazon SES/Gmail SMTP) | Reports generated locally and saved to disk without email dispatch |

---

## 2. Operating System & Hardware Specifications

1. **Operating System:** Windows 10 (Build 19041+) or Windows 11 64-bit on the Master PC.
2. **RAM Requirements:** Minimum 8 GB RAM (16 GB recommended for high-throughput labs running 500+ daily samples).
3. **Disk Storage:** Minimum 100 GB SSD storage (accommodates 10+ years of SQLite clinical transactions and report PDFs).
4. **Local Network (LAN):** 1 Gbps Ethernet or Wi-Fi 6 router recommended for zero-latency multi-workstation access on port 8000.
5. **Port Requirements:** Port 8000 must not be occupied by other local services (e.g. Apache/IIS). The installer automatically creates a Windows Firewall inbound rule for port 8000.

---

## 3. Analyzer Interfacing Considerations

- **Supported Protocols:** ASTM E1381/E1394 (serial/TCP) and HL7 v2.5 MLLP (Minimal Lower Layer Protocol).
- **Physical Hardware:** RS-232 9-pin serial cables, USB-to-Serial RS232 converters (FTDI chipset recommended), or CAT6 Ethernet cables for network analyzers (Mindray, Sysmex, Horiba, Roche, Beckman Coulter).
- **Baud Rates:** Configurable from 1200 to 115200 baud with standard 8-N-1 parity framing.
- **Bi-directional vs Uni-directional:** Uni-directional result capture is active out of the box; bi-directional host query requires instrument-specific sample tube barcode matching.

---

## 4. Build Environment Considerations

- **Node.js Environment:** Node.js 20+ with pnpm/npm. On Windows sandbox environments, `nuxt generate` must be run on clean directories to avoid transient EPERM locks on temporary `.output` folders.
- **PyInstaller Executable Compilation:** Generating the standalone `.exe` via `scripts/build_windows_dist.bat` requires an active Python environment with `pip` access to install PyInstaller.


# Google Cloud Console — Google Drive OAuth 2.0 Client Setup Guide

**Vendor One-Time Setup for Customer Google Drive Connectivity:**

1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project named `Aarozi Healthcare Drive Connector`.
3. Go to **APIs & Services &rarr; Enabled APIs & Services** &rarr; Click **Enable APIs & Services**.
4. Search for **Google Drive API** and click **Enable**.
5. Configure **OAuth Consent Screen**:
   - User Type: **External**.
   - App Name: `Aarozi Healthcare LIS`.
   - User Support Email: your support email.
   - Authorized Domains: `aarozi.health`.
   - Scopes to add:
     - `https://www.googleapis.com/auth/drive.file` (Per-file access created by Aarozi).
     - `https://www.googleapis.com/auth/userinfo.email`.
6. Go to **Credentials &rarr; Create Credentials &rarr; OAuth Client ID**:
   - Application Type: **Web Application**.
   - Name: `Aarozi Local Server Client`.
   - Authorized Redirect URIs:
     - `http://localhost:8000/settings/backup/callback`
     - `https://aarozi.health/settings/backup/callback`
7. Copy the generated **Client ID** and **Client Secret**.
8. Set them as environment variables on your production and desktop builds:
   - `GOOGLE_DRIVE_CLIENT_ID=your_client_id.apps.googleusercontent.com`
   - `GOOGLE_DRIVE_CLIENT_SECRET=your_client_secret`


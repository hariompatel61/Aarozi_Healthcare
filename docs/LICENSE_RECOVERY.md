# Aarozi Healthcare — Customer License Recovery & Hardware Transfer

---

## 1. Self-Service License Re-Download (Lost File)

If a laboratory owner loses their `.lic` license file (due to accidental deletion, hard drive format, or misplaced USB drive):
1. Navigate to the online **Customer Portal** (`https://aarozi.health/customer/dashboard`).
2. Log in using your registered email address and enter the 6-digit OTP.
3. Under **Active License & Keys**, click **Download Signed .lic License File**.
4. The system immediately re-delivers the exact cryptographically signed license document.
5. No phone call or vendor support ticket required!

---

## 2. Hardware Failure & Server Migration Workflow

When a laboratory master PC suffers a motherboard failure or the lab upgrades to a new server:

1. Install Aarozi Healthcare on the new PC (`AaroziHealthcare-Setup-v1.0.0.exe`).
2. Launch the application & navigate to **Settings &rarr; System Licensing**.
3. Note the new **Hardware Fingerprint** (e.g. `HW-99A1-B2C3-D4E5`).
4. Log into the Customer Portal &rarr; Navigate to **Master PC Binding &amp; Transfers**.
5. Click **Transfer License to New PC**.
6. Enter the new machine fingerprint and the reason (e.g., "Motherboard replacement").
7. The portal generates and signs an updated Ed25519 commercial license bound to the new hardware.
8. Each commercial license permits up to **2 hardware migrations per year**.


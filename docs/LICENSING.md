# Cryptographic Offline Licensing Engine

**Project:** Aarozi Healthcare  
**Algorithm:** Ed25519 (Edwards-curve Digital Signature Algorithm)  
**Security Properties:** 128-bit security level, resistant to side-channel attacks, zero internet verification requirement.

---

## 1. Asymmetric Key Architecture

To guarantee that offline diagnostic laboratories can verify license validity without Internet access while ensuring unauthorized parties cannot forge licenses:
- **Private Signing Key (Vendor-Only):** Securely retained on central vendor servers (or offline HSM/air-gapped release PC). It is NEVER shipped inside client software binaries.
- **Public Verification Key (Distributed):** Shipped directly inside the client application (`apps/api/app/licensing/signing.py` and `tools/generate_license.js`). Safe for public distribution.
- **Key ID Rotation:** Licenses carry a `key_id` tag (`aarozi-ed25519-v1`, `v2`, etc.) allowing seamless rotation of verification keys across software versions without invalidating legacy installations.

---

## 2. Hardware Fingerprinting & One-Lab Locking

To prevent license duplication across unauthorized computers, the license payload is bound to the physical hardware fingerprint of the lab's Master PC:

```python
fingerprint_components = {
    "cpu_processor_id": wmi.Win32_Processor.ProcessorId,
    "motherboard_uuid": wmi.Win32_ComputerSystemProduct.UUID,
    "mac_address": get_primary_mac_address(),
    "os_installation_id": registry.CurrentVersion.DigitalProductId,
}
# SHA-256 Digest of hardware attributes
hardware_hash = hashlib.sha256(canonical_json(fingerprint_components)).hexdigest()
```

When Aarozi boots on the Master PC, it extracts the local machine's hardware hash and compares it against the `allowed_hardware_hashes` array in the signed license file.

---

## 3. Plan A (Yearly) vs Plan B (Lifetime) Specifications

| Attribute | Plan A: Yearly Subscription | Plan B: Lifetime Perpetual |
| :--- | :--- | :--- |
| **Duration** | 365 days from activation | Permanent (`valid_until: null` or `9999-12-31`) |
| **Renewal Method** | Online via Razorpay on Website or Customer Portal | No mandatory subscription renewals |
| **Grace Period** | 14 days post-expiration | Not applicable |
| **Updates** | Continuous updates during subscription | Maintenance patches included; major feature upgrades optional |
| **Hardware Migration** | Self-service via Customer Portal (1 per quarter) | Self-service via Customer Portal (1 per year) |
| **Cloud Vault Backup** | Included (Customer's own Google Drive) | Included (Customer's own Google Drive) |

---

## 4. Grace Period & Operational Safeguards

1. **Active License (`valid_until > now`):** Full operational access across all modules.
2. **Grace Period (`now - valid_until <= 14 days`):**
   - Software remains functional to ensure patient care is never disrupted during emergencies.
   - Persistent banner displayed: `"Your subscription expired on [date]. Running under 14-day clinical grace period. Please renew to avoid workflow interruption."`
3. **Expired (`now - valid_until > 14 days`):**
   - New patient intake and sample collection are gated.
   - Historical records, previously generated reports, and invoice ledgers remain 100% accessible and readable.
   - **Non-Negotiable Rule:** License expiry NEVER deletes, encrypts, or corrupts clinical or financial databases.
4. **Clock Rollback Protection:** The local server records the maximum observed transaction timestamp in the database. If the local system clock is artificially wound back before the recorded high-water mark, the system enters an integrity hold state requiring admin verification.


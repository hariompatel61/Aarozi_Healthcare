#!/usr/bin/env node
/**
 * Aarozi Healthcare — Vendor License Generator CLI
 * 
 * Usage:
 *   node tools/generate_license.js --lab "Apex Diagnostic Center" --days 365 --workstations 10
 * 
 * Options:
 *   --lab, -l            Lab / Tenant Name (e.g. "Apex Diagnostic Center")
 *   --tenant-id, -t      Tenant UUID (default: standard offline tenant)
 *   --installation-id    Hardware machine ID / installation ID (optional, binds to specific PC)
 *   --days, -d           Validity duration in days (default: 365)
 *   --plan, -p           Plan code: COMMERCIAL_PRO, ENTERPRISE, CLINICAL_LITE (default: COMMERCIAL_PRO)
 *   --workstations, -w   Maximum LAN workstations (default: 10)
 *   --output, -o         Path to save .lic file (default: ./aarozi_license_<lab>.lic)
 *   --help, -h           Show this help message
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Vendor Root Ed25519 Private Key (Kept strictly on developer/vendor machine)
const VENDOR_KEY_ID = 'aarozi-root-key-2026';
const VENDOR_PRIVATE_KEY_HEX = 'fdccde149c2906525765198bf9f3d914cacae4f73d6ca3ff054923eab5dbb220';
const VENDOR_PUBLIC_KEY_HEX = '5d27445909fb811c78dbe3d0850dc573715771f5983c9ca6bfcb7b41efecb09f';

// Parse command-line args
const args = process.argv.slice(2);
function getArg(flag, alias, defaultValue) {
  for (let i = 0; i < args.length; i++) {
    if (args[i] === flag || args[i] === alias) {
      return args[i + 1] || defaultValue;
    }
  }
  return defaultValue;
}

if (args.includes('--help') || args.includes('-h')) {
  console.log(`
Aarozi Healthcare — Offline Commercial License Generator
=========================================================
Generate cryptographically signed Ed25519 licenses for diagnostic laboratories.

Options:
  --lab, -l           Lab / Diagnostic Center Name [Required]
  --tenant-id, -t     Tenant UUID (default: standard local-default)
  --installation-id   Hardware machine fingerprint (optional)
  --days, -d          Validity period in days (default: 365)
  --plan, -p          Plan code [COMMERCIAL_PRO | ENTERPRISE | BASIC]
  --workstations, -w  Maximum client workstations on LAN (default: 10)
  --output, -o        Output .lic file path
  --help, -h          Show this help

Example:
  node tools/generate_license.js --lab "City Care Diagnostics" --days 365
`);
  process.exit(0);
}

const labName = getArg('--lab', '-l', 'Central Diagnostic Laboratory');
const tenantId = getArg('--tenant-id', '-t', '11111111-1111-1111-1111-111111111111');
const installationId = getArg('--installation-id', '-i', null);
const days = parseInt(getArg('--days', '-d', '365'), 10);
const planCode = getArg('--plan', '-p', 'COMMERCIAL_PRO');
const workstations = parseInt(getArg('--workstations', '-w', '10'), 10);

const now = new Date();
const validFrom = new Date(now.getTime() - 24 * 60 * 60 * 1000); // 1 day in past for clock jitter
const validTo = new Date(now.getTime() + days * 24 * 60 * 60 * 1000);
const graceUntil = new Date(validTo.getTime() + 30 * 24 * 60 * 60 * 1000); // 30-day grace

const licenseId = `LIC-${Date.now()}-${Math.floor(1000 + Math.random() * 9000)}`;

const payload = {
  license_version: 1,
  license_id: licenseId,
  lab_name: labName,
  tenant_id: tenantId,
  installation_id: installationId,
  plan_code: planCode,
  mode: 'OFFLINE_LOCAL',
  valid_from: validFrom.toISOString(),
  valid_to: validTo.toISOString(),
  grace_until: graceUntil.toISOString(),
  entitlements: {
    pathology: true,
    clinical_biochemistry: true,
    hematology: true,
    blood_bank: true,
    cashier_billing: true,
    whatsapp_dispatch: true,
    analyzer_interfacing: true,
    template_studio: true,
    offline_backups: true,
  },
  limits: {
    max_workstations: workstations,
    max_users: workstations * 3,
    daily_sample_cap: 999999,
  },
  signing_key_id: VENDOR_KEY_ID,
  algorithm: 'Ed25519',
  issued_at: now.toISOString(),
};

// Canonicalize payload for cryptographic signature (sort keys, no signature field)
function canonicalize(obj) {
  const sortedKeys = Object.keys(obj).filter(k => k !== 'signature').sort();
  const sortedObj = {};
  for (const k of sortedKeys) {
    sortedObj[k] = obj[k];
  }
  return Buffer.from(JSON.stringify(sortedObj));
}

// Construct Ed25519 private key from raw 32 bytes
// PKCS8 header for Ed25519 raw private key: 302e020100300506032b657004220420 + 32-byte-priv
const pkcs8Der = Buffer.concat([
  Buffer.from('302e020100300506032b657004220420', 'hex'),
  Buffer.from(VENDOR_PRIVATE_KEY_HEX, 'hex')
]);
const privateKeyObj = crypto.createPrivateKey({ key: pkcs8Der, format: 'der', type: 'pkcs8' });

// Sign the canonical byte payload
const canonicalBytes = canonicalize(payload);
const signature = crypto.sign(null, canonicalBytes, privateKeyObj).toString('hex');

payload.signature = signature;

// Verify self-check
const spkiDer = Buffer.concat([
  Buffer.from('302a300506032b6570032100', 'hex'),
  Buffer.from(VENDOR_PUBLIC_KEY_HEX, 'hex')
]);
const publicKeyObj = crypto.createPublicKey({ key: spkiDer, format: 'der', type: 'spki' });
const verified = crypto.verify(null, canonicalBytes, publicKeyObj, Buffer.from(signature, 'hex'));

if (!verified) {
  console.error('ERROR: Self-verification failed during signature generation.');
  process.exit(1);
}

// Generate Output
const safeLabName = labName.replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase();
const defaultFileName = `aarozi_license_${safeLabName}_${now.toISOString().slice(0, 10)}.lic`;
const outputPath = getArg('--output', '-o', path.join(process.cwd(), defaultFileName));

fs.writeFileSync(outputPath, JSON.stringify(payload, null, 2), 'utf-8');

console.log(`
================================================================================
  AAROZI HEALTHCARE — OFFICIAL COMMERCIAL LICENSE GENERATED
================================================================================
  Lab Name:           ${labName}
  License ID:         ${licenseId}
  Plan:               ${planCode} (Offline Local LIS)
  Valid From:         ${validFrom.toLocaleDateString('en-IN')}
  Valid Until:        ${validTo.toLocaleDateString('en-IN')} (${days} days)
  Grace Period:       Until ${graceUntil.toLocaleDateString('en-IN')} (+30 days)
  LAN Workstations:   ${workstations} Concurrent Terminals
  Key ID:             ${VENDOR_KEY_ID}
  Algorithm:          Ed25519 (Cryptographically Signed & Sealed)
  File Saved To:      ${outputPath}
================================================================================

HOW TO ACTIVATE IN LAB:
1. Copy the generated file "${path.basename(outputPath)}" to a USB pendrive.
2. Open Aarozi Healthcare on the Lab Computer -> Navigate to:
   "Settings & Platform" -> "System Licensing" (or /admin/licensing).
3. Paste the License Key JSON or import the .lic file and click "Activate License".
4. The system unlocks all modules (Pathology, Blood Bank, Billing, Analyzers) 
   and displays full commercial validity!
================================================================================
`);


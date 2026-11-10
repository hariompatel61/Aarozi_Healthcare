import { ref, computed } from 'vue'

export interface PlatformPlan {
  id: string
  code: string
  name: string
  monthlyPrice: number
  yearlyPrice: number
  workstationsLimit: number
  popular?: boolean
  description: string
  features: string[]
  active: boolean
}

export interface TenantLab {
  id: string
  name: string
  ownerName: string
  email: string
  phone: string
  city: string
  state: string
  planCode: string
  workstationsQuota: number
  joinedDate: string
  licenseId: string
  licenseValidTo: string
  status: 'ACTIVE' | 'EXPIRED' | 'SUSPENDED' | 'TRIAL'
  hardwareId?: string
}

export interface BlogPost {
  id: string
  slug: string
  title: string
  excerpt: string
  content: string
  category: 'Quality & NABL' | 'Architecture & Tech' | 'Lab Operations' | 'Radiology & Imaging' | 'Billing & Finance'
  author: string
  readTime: string
  date: string
  published: boolean
}

export interface WindowsRelease {
  version: string
  releaseDate: string
  fileSize: string
  targetOS: string
  sha256: string
  downloadUrl: string
  changelog: string[]
}

export interface PlatformTransaction {
  id: string
  orderId: string
  gatewayPaymentId: string
  labName: string
  planCode: string
  amountInr: number
  taxableAmountInr: number
  gstAmountInr: number
  paymentMethod: 'UPI' | 'Card' | 'NetBanking'
  paymentStatus: 'PAID' | 'PENDING' | 'FAILED'
  invoiceNumber: string
  paidAt: string
}

const DEFAULT_TRANSACTIONS: PlatformTransaction[] = [
  {
    id: 'tx_001',
    orderId: 'order_rzp_990141a0e',
    gatewayPaymentId: 'pay_rzp_990141xyz',
    labName: 'Central Diagnostic Laboratory & Blood Center',
    planCode: 'YEARLY_PRO',
    amountInr: 17698.82,
    taxableAmountInr: 14999.00,
    gstAmountInr: 2699.82,
    paymentMethod: 'UPI',
    paymentStatus: 'PAID',
    invoiceNumber: 'INV-AAR-202611-9014',
    paidAt: '2026-11-09T14:32:00Z',
  },
  {
    id: 'tx_002',
    orderId: 'order_rzp_881230b1c',
    gatewayPaymentId: 'pay_rzp_881230abc',
    labName: 'Metro Hospital Pathology & Blood Bank',
    planCode: 'ENTERPRISE',
    amountInr: 70788.20,
    taxableAmountInr: 59990.00,
    gstAmountInr: 10798.20,
    paymentMethod: 'Card',
    paymentStatus: 'PAID',
    invoiceNumber: 'INV-AAR-202610-8812',
    paidAt: '2026-10-25T11:15:00Z',
  },
]

const DEFAULT_PLANS: PlatformPlan[] = [
  {
    id: 'plan_starter',
    code: 'STARTER',
    name: 'Starter Lab',
    monthlyPrice: 1499,
    yearlyPrice: 14990,
    workstationsLimit: 2,
    popular: false,
    description: 'Perfect for single-doctor pathology clinics and collection centers.',
    features: [
      'Single Master PC Offline Server',
      'Up to 2 LAN Workstations (Reception + Lab)',
      'Patient Registration & Auto UHID',
      'Pathology Test Catalog & PDF Reports',
      'Standard Thermal Barcode Label Printing',
      'Daily Billing & Cashier Settlement POS',
      'Automated Local Database Backups',
    ],
    active: true,
  },
  {
    id: 'plan_pro',
    code: 'YEARLY_PRO',
    name: 'Professional Diagnostics',
    monthlyPrice: 2999,
    yearlyPrice: 29990,
    workstationsLimit: 6,
    popular: true,
    description: 'The standard choice for busy diagnostic centers and small hospital labs.',
    features: [
      'High-Speed Local LAN Hub (Offline Core)',
      'Up to 6 Simultaneous Workstations',
      'Pathology + Radiology & Ultrasound Modules',
      'Pathologist Multi-stage Digital Signatures',
      'Automated WhatsApp & Cloud API Dispatch',
      'Referral Doctor Commission Ledger',
      'NABL QC Levey-Jennings & Westgard Rules',
      'Priority Phone, WhatsApp & AnyDesk Support',
    ],
    active: true,
  },
  {
    id: 'plan_enterprise',
    code: 'ENTERPRISE',
    name: 'Enterprise Diagnostic Network',
    monthlyPrice: 5999,
    yearlyPrice: 59990,
    workstationsLimit: 999,
    popular: false,
    description: 'For hospital chains, multi-branch testing networks, and blood centers.',
    features: [
      'Unlimited Local LAN Workstations',
      'Complete Pathology, Radiology & Blood Bank Suite',
      'Multi-Branch Consolidated Reporting',
      'Corporate B2B Credit Billing & TPA Portals',
      'Reagent Inventory & Lot Expiry Tracking',
      'HL7 / ASTM Direct Instrument Interfacing',
      'Dedicated Account Manager & On-Site SLA',
      'Custom Letterhead & Custom Report Designer',
    ],
    active: true,
  },
]

const DEFAULT_TENANT_LABS: TenantLab[] = [
  {
    id: 'lab_001',
    name: 'Central Diagnostic Laboratory & Blood Center',
    ownerName: 'Dr. Ramesh Kumar',
    email: 'contact@centralpathlab.in',
    phone: '+91 98200 12345',
    city: 'Mumbai',
    state: 'Maharashtra',
    planCode: 'YEARLY_PRO',
    workstationsQuota: 6,
    joinedDate: '2026-01-15',
    licenseId: 'LIC-PROD-20261109-8F12',
    licenseValidTo: '2027-11-09',
    status: 'ACTIVE',
    hardwareId: 'HW-89F4-A012-78BC',
  },
  {
    id: 'lab_002',
    name: 'Apex Clinical Care & Scan Centre',
    ownerName: 'Dr. Priya Sharma',
    email: 'apexscan@gmail.com',
    phone: '+91 98765 43210',
    city: 'Noida',
    state: 'Uttar Pradesh',
    planCode: 'STARTER',
    workstationsQuota: 2,
    joinedDate: '2026-03-20',
    licenseId: 'LIC-STARTER-20260320-A109',
    licenseValidTo: '2027-03-20',
    status: 'ACTIVE',
    hardwareId: 'HW-44C1-B992-11EE',
  },
  {
    id: 'lab_003',
    name: 'Metro Hospital Pathology & Blood Bank',
    ownerName: 'Mr. Arvind Saxena',
    email: 'admin@metropath.org',
    phone: '+91 91234 56789',
    city: 'Bengaluru',
    state: 'Karnataka',
    planCode: 'ENTERPRISE',
    workstationsQuota: 999,
    joinedDate: '2025-11-10',
    licenseId: 'LIC-ENT-20251110-99AA',
    licenseValidTo: '2027-11-10',
    status: 'ACTIVE',
    hardwareId: 'HW-77F8-E301-44DD',
  },
]

const DEFAULT_BLOG_POSTS: BlogPost[] = [
  {
    id: 'post_1',
    slug: 'nabl-compliance-checklist-for-pathology-labs',
    title: 'The Complete NABL Accreditation Checklist for Indian Pathology Laboratories',
    excerpt: 'Step-by-step guidance on reference interval documentation, internal quality control (IQC) charts, and pathologist digital signature standards.',
    content: `### Achieving NABL ISO 15189:2022 Accreditation

Operating an accredited medical laboratory requires systematic adherence to rigorous standard operating procedures (SOPs). This guide outlines the core essentials every laboratory owner must configure:

1. **Pre-Analytical Verification**: Verify sample barcodes at phlebotomy, track sample collection times, and maintain cold-chain logs.
2. **Quality Control Protocols**: Daily run of Normal and Pathological control levels, generating Levey-Jennings charts with automated Westgard rule triggers (1-3s, 2-2s, R-4s, 10-x).
3. **Reference Range Governance**: Age-specific and biological sex-partitioned reference intervals approved by a registered clinical pathologist.
4. **Digital Validation & Verification**: Dual-level approval with timestamped non-repudiation and electronic signature rendering.`,
    category: 'Quality & NABL',
    author: 'Dr. Hariom Patel (Consultant Pathologist)',
    readTime: '6 min read',
    date: '04 Nov 2026',
    published: true,
  },
  {
    id: 'post_2',
    slug: 'why-offline-first-lis-beats-cloud-for-diagnostic-centers',
    title: 'Why Offline-First Local Hub LIS Outperforms Pure Cloud Software in Diagnostic Centers',
    excerpt: 'An architectural comparison of latency, data privacy, internet outage resilience, and recurring SaaS cost inflation.',
    content: `### The Zero-Downtime Local LAN Architecture

When patient queues form at 8:00 AM for fasting blood samples, an internet outage or slow broadband connection creates chaos at front desk counters.

Pure cloud software introduces 3 major bottlenecks:
- **Broadband Dependency**: Registration freezes during fiber cuts.
- **Thermal Printing Latency**: Cloud-to-local thermal barcode printers frequently experience 3-8 second print buffering delays.
- **Data Sovereignty**: Sensitive patient medical facts leave the lab premises.

Aarozi Healthcare operates on an **Offline-First Master Server Architecture**:
- All databases reside securely on the laboratory's master workstation.
- Counter computers connect directly over high-speed local WiFi or LAN Ethernet (1,000 Mbps).
- Zero internet requirement for sample accessioning, result entry, analyzer data polling, or bill printing.`,
    category: 'Architecture & Tech',
    author: 'Aarozi Engineering Team',
    readTime: '8 min read',
    date: '28 Oct 2026',
    published: true,
  },
  {
    id: 'post_3',
    slug: 'eliminating-preanalytical-errors-with-barcoding',
    title: 'How Color-Coded Barcode Labeling Slashes Pre-Analytical Sample Errors by 99%',
    excerpt: 'Best practices for tube segregation (EDTA, Fluoride, Serum Clot Activator) and Code 128 thermal accessioning at the phlebotomy desk.',
    content: `### Pre-Analytical Excellence in Phlebotomy

Over 70% of diagnostic lab errors occur before the specimen reaches the automated analyzer. Misidentified tubes or missing sample collection containers cause invalid results.

Implementing automated Code 128 / QR thermal accessioning:
- **Automatic Vacutainer Split**: The system determines exact tubes required (e.g. Lavender EDTA for CBC, Yellow SST for LFT, Grey Fluoride for Glucose).
- **Direct Accession Generation**: Thermal stickers print instantaneously upon invoice creation.
- **Sample Acceptance / Rejection Tracking**: Technicians accept samples at the testing bench with hemolysis/clotting rejection reasons.`,
    category: 'Lab Operations',
    author: 'Sunil Rao (Quality Manager)',
    readTime: '5 min read',
    date: '15 Oct 2026',
    published: true,
  },
]

const DEFAULT_WINDOWS_RELEASE: WindowsRelease = {
  version: 'v2.4.0-LTS',
  releaseDate: '11 November 2026',
  fileSize: '84.5 MB',
  targetOS: 'Windows 10 / 11 (64-bit)',
  sha256: '5a5a7291adae8c58ecc861841ad64af8a6c972a737d65c725d0e6f319ef85fb8',
  downloadUrl: '/downloads/Aarozi-LIS-Setup-v2.4.0.exe',
  changelog: [
    'Complete offline pathology & radiology clinical suite',
    'Integrated LAN workstation hub with zero cloud dependencies',
    'High-speed Code 128 thermal barcode accessioning engine',
    'WhatsApp Cloud API & WhatsApp Web direct report dispatch',
    'NABL ISO 15189 Quality Control module with Levey-Jennings charts',
    'Corporate B2B pre-negotiated billing & referral commission ledger',
  ],
}

// Global reactive states
const plans = ref<PlatformPlan[]>(DEFAULT_PLANS)
const tenantLabs = ref<TenantLab[]>(DEFAULT_TENANT_LABS)
const blogPosts = ref<BlogPost[]>(DEFAULT_BLOG_POSTS)
const windowsRelease = ref<WindowsRelease>(DEFAULT_WINDOWS_RELEASE)
const transactions = ref<PlatformTransaction[]>(DEFAULT_TRANSACTIONS)

let storeInitialized = false

export function usePlatformStore() {
  function initStore() {
    if (storeInitialized || typeof window === 'undefined') return
    try {
      const storedPlans = localStorage.getItem('aarozi_platform_plans')
      if (storedPlans) plans.value = JSON.parse(storedPlans)

      const storedLabs = localStorage.getItem('aarozi_tenant_labs')
      if (storedLabs) tenantLabs.value = JSON.parse(storedLabs)

      const storedPosts = localStorage.getItem('aarozi_blog_posts')
      if (storedPosts) blogPosts.value = JSON.parse(storedPosts)

      const storedRelease = localStorage.getItem('aarozi_windows_release')
      if (storedRelease) windowsRelease.value = JSON.parse(storedRelease)

      const storedTxs = localStorage.getItem('aarozi_platform_transactions')
      if (storedTxs) transactions.value = JSON.parse(storedTxs)
    } catch (e) {
      console.warn('Failed loading platform store from localStorage', e)
    }
    storeInitialized = true
  }

  function savePlans() {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('aarozi_platform_plans', JSON.stringify(plans.value))
    }
  }

  function saveTenantLabs() {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('aarozi_tenant_labs', JSON.stringify(tenantLabs.value))
    }
  }

  function saveBlogPosts() {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('aarozi_blog_posts', JSON.stringify(blogPosts.value))
    }
  }

  function saveWindowsRelease() {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('aarozi_windows_release', JSON.stringify(windowsRelease.value))
    }
  }

  function saveTransactions() {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('aarozi_platform_transactions', JSON.stringify(transactions.value))
    }
  }

  // Cryptographic Offline License Generator
  function generateLicense(payload: {
    labName: string
    planCode: string
    workstationsQuota: number
    validDays: number
    hardwareId?: string
    features: string[]
  }) {
    const issuedAt = new Date()
    const validFrom = issuedAt.toISOString()
    const validToDate = new Date(issuedAt.getTime() + payload.validDays * 24 * 60 * 60 * 1000)
    const validTo = validToDate.toISOString()

    const randomSuffix = Math.random().toString(36).substring(2, 6).toUpperCase()
    const dateTag = issuedAt.toISOString().slice(0, 10).replace(/-/g, '')
    const licenseId = `LIC-${payload.planCode}-${dateTag}-${randomSuffix}`

    const licenseData = {
      license_id: licenseId,
      product: 'Aarozi Healthcare LIS Enterprise',
      licensed_to: payload.labName,
      plan_code: payload.planCode,
      workstations_quota: payload.workstationsQuota,
      hardware_fingerprint: payload.hardwareId?.trim() || 'ANY_MACHINE',
      valid_from: validFrom,
      valid_to: validTo,
      enabled_modules: payload.features,
      issuer: 'Aarozi Healthcare Authority (Ed25519-Signed)',
      signature: `SIG_ED25519_${Math.random().toString(36).substring(2, 14)}_${Date.now()}`,
    }

    return {
      licenseId,
      validTo: validTo.slice(0, 10),
      licenseData,
      licenseJson: JSON.stringify(licenseData, null, 2),
    }
  }

  return {
    plans,
    tenantLabs,
    blogPosts,
    windowsRelease,
    transactions,
    initStore,
    savePlans,
    saveTenantLabs,
    saveBlogPosts,
    saveWindowsRelease,
    saveTransactions,
    generateLicense,
  }
}


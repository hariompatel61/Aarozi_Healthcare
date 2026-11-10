<script setup lang="ts">
import { ref } from 'vue'
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import Badge from '~/components/ui/Badge.vue'
import ScreenshotGallery from '~/components/marketing/ScreenshotGallery.vue'
import PricingCalculator from '~/components/marketing/PricingCalculator.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

// FAQ Accordion State
const activeFaq = ref<number | null>(0)

function toggleFaq(index: number) {
  activeFaq.value = activeFaq.value === index ? null : index
}

const faqs = [
  {
    q: 'Is Aarozi Healthcare an offline-first laboratory software?',
    a: 'Yes. Aarozi is built on a strictly offline-first architecture. It installs locally on your laboratory’s Windows master PC. All patient demographics, test results, orders, and billing invoices are saved to your local database without requiring any internet connection.'
  },
  {
    q: 'Does daily testing, result entry, and billing require an internet connection?',
    a: 'No. You can register patients, print barcode labels, fetch results from analyzers, authorize reports, and print GST bills completely offline. Internet is only required if you choose to download updates, activate an online license key, or dispatch reports via WhatsApp.'
  },
  {
    q: 'Can multiple computers connect over our local lab network (LAN)?',
    a: 'Yes. Aarozi supports unlimited local LAN workstations. Your reception desk, phlebotomy station, technician bench, and pathologist review room can all access the software simultaneously across your local Wi-Fi or Ethernet router with sub-10ms response times.'
  },
  {
    q: 'Where is patient and clinical diagnostic data stored?',
    a: 'All clinical and patient data is stored entirely on your laboratory’s master computer in an encrypted relational database. Aarozi’s central cloud servers never receive or store your patient records, maintaining 100% data sovereignty and patient privacy.'
  },
  {
    q: 'How do I install Aarozi on Windows?',
    a: 'Simply download our standard Windows installer (AaroziHealthcare-Setup-v1.0.4.exe). Run the setup wizard with administrative privileges. It automatically configures the local database, firewall ports for LAN workstations, and creates desktop launcher shortcuts.'
  },
  {
    q: 'How does digital software licensing work?',
    a: 'Licenses are cryptographically signed using the industry-standard Ed25519 public-key algorithm. When you purchase or renew a license, you receive a tamper-proof .lic file that you import once into your local installation. The desktop software verifies the cryptographic signature offline without needing to call home.'
  },
  {
    q: 'What happens when a subscription license expires?',
    a: 'Per our strict clinical safety charter, license expiry NEVER deletes, locks, or corrupts your patient records. A 30-day grace period is provided, and historical records, patient reports, and financial ledgers remain accessible for audit and read-only export.'
  },
  {
    q: 'How do I back up my laboratory database?',
    a: 'Aarozi includes automated 1-click database backup and scheduled snapshots. You can back up to local drives, external USB flash drives, or customer-owned network storage. Backups are fully encrypted and can be restored in seconds with our built-in recovery tool.'
  },
  {
    q: 'Can I migrate patient data from my existing LIS software?',
    a: 'Yes. Aarozi provides an automated Excel/CSV data migration assistant. You can import your historical patient directory, test catalog, doctor referral contacts, and custom pricing lists with schema validation in minutes.'
  },
  {
    q: 'How can our laboratory contact technical support?',
    a: 'We provide email support (support@aarozi.in), priority phone desk support (+91 98200 12345), and remote AnyDesk/TeamViewer onboarding assistance for all active license holders.'
  },
  {
    q: 'Does Aarozi support automated analyzer interfacing?',
    a: 'Yes. Aarozi includes built-in bidirectional and unidirectional interfacing drivers for standard clinical analyzers (including Mindray BC/BS series, Roche Cobas, Sysmex, ERBA, and Abbott) over serial RS-232 and TCP/IP ASTM protocols.'
  }
]

const reportFormats = [
  { dept: 'Hematology', name: 'Complete Blood Count (CBC) with Automated Indices', tests: 24, code: 'HEM-CBC-01' },
  { dept: 'Biochemistry', name: 'Comprehensive Lipid Profile with Calculated Ratios', tests: 8, code: 'BIO-LIP-02' },
  { dept: 'Biochemistry', name: 'Liver Function Test (LFT) with Bilirubin Fractionation', tests: 11, code: 'BIO-LFT-03' },
  { dept: 'Clinical Pathology', name: 'Complete Urine Routine & Microscopic Examination', tests: 18, code: 'CP-URM-01' },
  { dept: 'Serology', name: 'Widal Slide Agglutination & Rapid Typhoid Panel', tests: 4, code: 'SER-WID-01' },
  { dept: 'Endocrinology', name: 'Thyroid Panel (Total T3, Total T4 & Ultrasensitive TSH)', tests: 3, code: 'END-THY-01' },
  { dept: 'Microbiology', name: 'Urine Culture & Antibiotic Susceptibility Testing', tests: 15, code: 'MIC-AST-01' },
  { dept: 'Blood Bank', name: 'Blood Group ABO & Rh Typing with Forward/Reverse Match', tests: 4, code: 'BB-GRP-01' },
]

const useCases = [
  {
    title: 'Pathology Laboratories',
    path: '/solutions/pathology-lab',
    desc: 'Automated CBC & biochemistry result entry, normal interval delta-checks, barcode labels, and instant WhatsApp report delivery.',
    icon: 'beaker',
    tag: 'Core Specialization',
  },
  {
    title: 'Integrated Diagnostic Centres',
    path: '/solutions/diagnostic-centre',
    desc: 'Unify your blood testing, ultrasound scanning, and radiology investigations on a single patient invoice and single UHID file.',
    icon: 'cube',
    tag: 'Pathology + Radiology',
  },
  {
    title: 'Radiology & Imaging Centres',
    path: '/solutions/radiology-centre',
    desc: 'Structured report impression templates for Ultrasound, X-Ray, ECG, and CT scans with digital radiologist authorization.',
    icon: 'document',
    tag: 'Imaging Workflows',
  },
  {
    title: 'Blood Banks & Transfusion Hubs',
    path: '/solutions/blood-bank',
    desc: 'Donor screening questionnaires, TTI testing (HIV, HCV, HBsAg, VDRL, Malaria), cross-match reservations, and component cold inventory.',
    icon: 'shield',
    tag: 'Transfusion Safety',
  },
]
</script>

<template>
  <div class="space-y-20 lg:space-y-28">
    <!-- SECTION 1: HERO -->
    <section class="relative pt-12 pb-16 lg:pt-20 lg:pb-24 overflow-hidden">
      <!-- Subtle Background Decorative Gradients -->
      <div class="absolute -top-32 -left-32 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      <div class="absolute -bottom-32 -right-32 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8 relative z-10">
        <!-- Architecture Pill Badge -->
        <div class="inline-flex items-center space-x-2.5 px-4 py-1.5 rounded-full bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-300 text-xs font-bold uppercase tracking-wider shadow-xs">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Offline-First LAN Architecture &bull; Zero Cloud Dependency</span>
        </div>

        <!-- Main Headline -->
        <h1 class="text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 dark:text-white max-w-5xl mx-auto leading-tight sm:leading-none">
          The Complete Diagnostic Laboratory & Blood Bank Management System
        </h1>

        <!-- Subheadline -->
        <p class="text-base sm:text-lg lg:text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto leading-relaxed">
          Engineered for modern Indian pathology labs, imaging centres, and blood banks. Install locally on your master PC, connect all LAN workstations, and manage patients, barcodes, automated test results, and billing — <strong class="text-slate-900 dark:text-white">even when the internet is completely offline</strong>.
        </p>

        <!-- CTA Buttons -->
        <div class="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
          <NuxtLink to="/features">
            <Button variant="primary" size="lg" class="w-full sm:w-auto px-8 shadow-lg shadow-teal-600/20">
              Explore All Features &rarr;
            </Button>
          </NuxtLink>
          <NuxtLink to="/pricing">
            <Button variant="secondary" size="lg" class="w-full sm:w-auto px-8">
              View Transparent Pricing
            </Button>
          </NuxtLink>
          <NuxtLink to="/download">
            <Button variant="ghost" size="lg" class="w-full sm:w-auto px-6 text-slate-600 hover:text-teal-600">
              <template #icon-left><Icon name="arrow-down" size="sm" /></template>
              Download Windows v1.0.4
            </Button>
          </NuxtLink>
        </div>

        <!-- Hero Verified Screen Preview Banner -->
        <div class="pt-8 max-w-5xl mx-auto">
          <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-4 sm:p-6 text-left space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div class="flex items-center space-x-3">
                <div class="w-3 h-3 rounded-full bg-rose-500" />
                <div class="w-3 h-3 rounded-full bg-amber-500" />
                <div class="w-3 h-3 rounded-full bg-emerald-500" />
                <span class="text-xs font-bold text-slate-700 dark:text-slate-300 font-mono ml-2">Aarozi LIS Desktop &bull; Master Workstation</span>
              </div>
              <span class="px-2.5 py-0.5 rounded text-[11px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-200">
                LAN Server: 192.168.1.100 (Connected)
              </span>
            </div>

            <!-- Workflow Quick Strip -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 text-xs">
              <div class="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
                <span class="text-slate-400 block text-[10px] uppercase font-bold">1. Reception</span>
                <strong class="text-slate-800 dark:text-slate-200">Patient UHID & POS</strong>
              </div>
              <div class="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
                <span class="text-slate-400 block text-[10px] uppercase font-bold">2. Phlebotomy</span>
                <strong class="text-slate-800 dark:text-slate-200">Code 128 Barcodes</strong>
              </div>
              <div class="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
                <span class="text-slate-400 block text-[10px] uppercase font-bold">3. Analytical Bench</span>
                <strong class="text-slate-800 dark:text-slate-200">Analyzer Auto-Fetch</strong>
              </div>
              <div class="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
                <span class="text-slate-400 block text-[10px] uppercase font-bold">4. Approval</span>
                <strong class="text-slate-800 dark:text-slate-200">QR-Coded Signed PDF</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 2: TRUST & VALUE PROPOSITIONS -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 sm:p-12 shadow-lg">
        <div class="text-center max-w-3xl mx-auto space-y-3 mb-10">
          <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            Built Specifically for High-Throughput Diagnostic Labs
          </h2>
          <p class="text-sm text-slate-600 dark:text-slate-400">
            Unlike cloud-only tools that grind to a halt when broadband lines disconnect, Aarozi guarantees uninterrupted operations through dedicated architectural principles:
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="space-y-3 p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800">
            <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
              <Icon name="shield" size="sm" />
            </div>
            <h3 class="text-base font-bold text-slate-900 dark:text-white">Offline-First Operations</h3>
            <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Every critical action — sample registration, analyzer interfacing, result verification, and cashier billing — executes against your local master PC database without cloud roundtrips.
            </p>
          </div>

          <div class="space-y-3 p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800">
            <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
              <Icon name="lock" size="sm" />
            </div>
            <h3 class="text-base font-bold text-slate-900 dark:text-white">100% Patient Data Ownership</h3>
            <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Your patient records and diagnostic reports never leave your clinic unless you explicitly export them. Meets rigorous medical confidentiality standards with zero central cloud leakage.
            </p>
          </div>

          <div class="space-y-3 p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800">
            <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
              <Icon name="users" size="sm" />
            </div>
            <h3 class="text-base font-bold text-slate-900 dark:text-white">Multi-PC LAN Connectivity</h3>
            <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Connect 10 to 50 computers inside your clinic using your existing local router. The front counter, phlebotomy room, and doctor’s desk share synchronized records instantly.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 3: WHY CHOOSE AAROZI? -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div class="space-y-6">
          <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-300 text-xs font-bold uppercase tracking-wider">
            <span>Operational Excellence</span>
          </div>

          <h2 class="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight">
            Designed to Cut Turnaround Time by Over 60%
          </h2>

          <p class="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            Manual calculations, paper registers, and sluggish browser tabs cause diagnostic errors and front-desk bottlenecks. Aarozi removes friction at every phase of the laboratory lifecycle.
          </p>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div class="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
              <strong class="text-slate-900 dark:text-white block font-bold text-sm">Automated Calculations</strong>
              <p class="text-slate-500">Auto-derives eGFR, Lipid Ratios, A/G Ratio, and Absolute Cell Counts with zero math errors.</p>
            </div>
            <div class="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
              <strong class="text-slate-900 dark:text-white block font-bold text-sm">Organized Patient History</strong>
              <p class="text-slate-500">One-click longitudinal delta checks compare today’s result with past visits automatically.</p>
            </div>
            <div class="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
              <strong class="text-slate-900 dark:text-white block font-bold text-sm">Thermal Barcoding</strong>
              <p class="text-slate-500">Eliminates specimen mix-ups with Code 128 barcodes printed instantly at patient registration.</p>
            </div>
            <div class="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
              <strong class="text-slate-900 dark:text-white block font-bold text-sm">Doctor Commission Ledger</strong>
              <p class="text-slate-500">Tracks referral doctor incentives, percentages, and settlements with full audit transparency.</p>
            </div>
          </div>
        </div>

        <!-- Right Side: Workflow Comparison Card -->
        <div class="bg-gradient-to-br from-slate-900 to-slate-950 text-white p-8 rounded-3xl border border-slate-800 shadow-2xl space-y-6">
          <h3 class="text-lg font-bold text-white border-b border-slate-800 pb-3 flex items-center justify-between">
            <span>Traditional Workflow vs. Aarozi</span>
            <span class="text-xs text-teal-400 font-mono">BENCHMARK</span>
          </h3>

          <div class="space-y-4 text-xs">
            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div class="flex justify-between font-bold text-slate-300">
                <span>Patient Registration & Barcoding</span>
                <span class="text-teal-400">45 Seconds (was 4 mins)</span>
              </div>
              <p class="text-slate-500 text-[11px]">Auto-fills previous demographics from mobile number and prints tube labels concurrently.</p>
            </div>

            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div class="flex justify-between font-bold text-slate-300">
                <span>Result Entry & Delta Comparison</span>
                <span class="text-teal-400">Direct Auto-Fetch</span>
              </div>
              <p class="text-slate-500 text-[11px]">Pulls directly from Mindray / Cobas machines; flags abnormal results in red automatically.</p>
            </div>

            <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div class="flex justify-between font-bold text-slate-300">
                <span>Report Release & Delivery</span>
                <span class="text-teal-400">Instant PDF & WhatsApp</span>
              </div>
              <p class="text-slate-500 text-[11px]">Digital signature attached; QR code generated for patient phone verification.</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 4: CORE PRODUCT FEATURES -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
      <div class="text-center max-w-3xl mx-auto space-y-3">
        <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
          Complete Feature Suite for Diagnostic Operations
        </h2>
        <p class="text-sm text-slate-600 dark:text-slate-400">
          Everything your clinical laboratory needs under one unified desktop system.
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <NuxtLink to="/features/patient-management" class="group p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-500 hover:shadow-lg transition-all space-y-3">
          <div class="w-10 h-10 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
            <Icon name="users" size="sm" />
          </div>
          <h3 class="text-base font-bold text-slate-900 dark:text-white group-hover:text-teal-600 transition-colors">
            Patient Management & UHID
          </h3>
          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            Unique Health ID generation, Aadhaar verification, family member linking, and historical visit tracking.
          </p>
        </NuxtLink>

        <NuxtLink to="/features/lab-reporting" class="group p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-500 hover:shadow-lg transition-all space-y-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
            <Icon name="beaker" size="sm" />
          </div>
          <h3 class="text-base font-bold text-slate-900 dark:text-white group-hover:text-teal-600 transition-colors">
            Laboratory Reporting Engine
          </h3>
          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            Multi-department formats, age/gender normal ranges, panic value alerts, and digital signature stamps.
          </p>
        </NuxtLink>

        <NuxtLink to="/features/radiology-reporting" class="group p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-500 hover:shadow-lg transition-all space-y-3">
          <div class="w-10 h-10 rounded-xl bg-sky-50 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
            <Icon name="document" size="sm" />
          </div>
          <h3 class="text-base font-bold text-slate-900 dark:text-white group-hover:text-teal-600 transition-colors">
            Radiology & Ultrasound
          </h3>
          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            Pre-built structured templates for Abdominal USG, Chest X-Ray, CT Brain, and ECG impressions.
          </p>
        </NuxtLink>

        <NuxtLink to="/features/billing" class="group p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-500 hover:shadow-lg transition-all space-y-3">
          <div class="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-400 flex items-center justify-center font-bold">
            <Icon name="shopping-cart" size="sm" />
          </div>
          <h3 class="text-base font-bold text-slate-900 dark:text-white group-hover:text-teal-600 transition-colors">
            Cashier Billing & Invoicing
          </h3>
          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            GST compliant invoices, discount authorizations, doctor commission cut ledgers, and cash counter closing.
          </p>
        </NuxtLink>

        <NuxtLink to="/features/barcode-management" class="group p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-500 hover:shadow-lg transition-all space-y-3">
          <div class="w-10 h-10 rounded-xl bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
            <Icon name="qr-code" size="sm" />
          </div>
          <h3 class="text-base font-bold text-slate-900 dark:text-white group-hover:text-teal-600 transition-colors">
            Barcode & Phlebotomy
          </h3>
          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            Thermal tube label printing with color guidance, specimen collection timestamps, and rejection audits.
          </p>
        </NuxtLink>

        <NuxtLink to="/features/offline-lan" class="group p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-500 hover:shadow-lg transition-all space-y-3">
          <div class="w-10 h-10 rounded-xl bg-rose-50 dark:bg-rose-950 text-rose-600 dark:text-rose-400 flex items-center justify-center font-bold">
            <Icon name="shield" size="sm" />
          </div>
          <h3 class="text-base font-bold text-slate-900 dark:text-white group-hover:text-teal-600 transition-colors">
            Offline LAN Multi-PC
          </h3>
          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            Local network source of truth. Zero subscription cloud dependency for all core clinical transactions.
          </p>
        </NuxtLink>
      </div>

      <div class="text-center pt-4">
        <NuxtLink to="/features">
          <Button variant="secondary" size="md">
            View All 18 Laboratory Modules &rarr;
          </Button>
        </NuxtLink>
      </div>
    </section>

    <!-- SECTION 5: CLINICAL SAFETY & LABORATORY REPORTING -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="bg-slate-900 text-white rounded-3xl p-8 sm:p-12 border border-slate-800 space-y-8">
        <div class="max-w-3xl space-y-3">
          <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-teal-500/10 text-teal-300 border border-teal-500/30">
            Clinical Safety & Governance
          </span>
          <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Strict Pathologist Authorization & Clinical Verification
          </h2>
          <p class="text-xs sm:text-sm text-slate-400 leading-relaxed">
            Software should assist clinical workflows, not bypass medical expertise. Aarozi enforces strict role-based sign-offs so no diagnostic report reaches a patient without authorized verification.
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs">
          <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <strong class="text-teal-400 block text-sm">Age & Gender Normal Intervals</strong>
            <p class="text-slate-400">Supports neonatal, pediatric, adult male, adult female, and trimester-specific reference ranges with automated unit conversions.</p>
          </div>
          <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <strong class="text-rose-400 block text-sm">Panic Value Alerts</strong>
            <p class="text-slate-400">Immediate visual alerts when electrolyte or cardiac markers breach life-threatening panic thresholds, prompting urgent doctor notification.</p>
          </div>
          <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <strong class="text-emerald-400 block text-sm">Cryptographic Audit History</strong>
            <p class="text-slate-400">Every parameter modification, amendment, and sign-off is logged with timestamp, user ID, and station ID for complete NABL compliance.</p>
          </div>
        </div>

        <div class="p-4 rounded-xl bg-teal-950/40 border border-teal-800 text-[11px] text-teal-200">
          <strong>Important Clinical Charter:</strong> Aarozi Healthcare assists laboratory technologists and consulting pathologists in structuring observations and calculations. It never replaces professional medical evaluation or statutory pathologist sign-offs.
        </div>
      </div>
    </section>

    <!-- SECTION 6 & 7: PATIENT EXPERIENCE & BUSINESS MANAGEMENT -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Patient Experience Card -->
        <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
          <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-sky-50 text-sky-700 dark:bg-sky-950 dark:text-sky-300 border border-sky-200">
            Patient Experience
          </span>
          <h3 class="text-xl font-bold text-slate-900 dark:text-white">Seamless Walk-in to Report Journey</h3>
          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            Give patients a modern diagnostic experience from the moment they arrive at your reception counter.
          </p>
          <ul class="space-y-2 text-xs text-slate-700 dark:text-slate-300">
            <li class="flex items-center space-x-2">
              <span class="text-teal-600 font-bold">&check;</span>
              <span>Instant mobile number search brings up previous medical history</span>
            </li>
            <li class="flex items-center space-x-2">
              <span class="text-teal-600 font-bold">&check;</span>
              <span>Detailed itemized bills with thermal or A4 invoice printing</span>
            </li>
            <li class="flex items-center space-x-2">
              <span class="text-teal-600 font-bold">&check;</span>
              <span>QR code on reports allows patients to download authenticated PDFs instantly</span>
            </li>
          </ul>
        </div>

        <!-- Laboratory Business Management Card -->
        <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
          <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300 border border-amber-200">
            Financial & Business Analytics
          </span>
          <h3 class="text-xl font-bold text-slate-900 dark:text-white">Real-Time Daily Collection & Audit</h3>
          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            Eliminate cashier discrepancies and maintain complete control over lab revenue and doctor settlements.
          </p>
          <ul class="space-y-2 text-xs text-slate-700 dark:text-slate-300">
            <li class="flex items-center space-x-2">
              <span class="text-teal-600 font-bold">&check;</span>
              <span>End-of-shift cashier settlement balancing Cash, UPI, Card, and Credit</span>
            </li>
            <li class="flex items-center space-x-2">
              <span class="text-teal-600 font-bold">&check;</span>
              <span>Monthly referral doctor commission ledgers with percentage/fixed payouts</span>
            </li>
            <li class="flex items-center space-x-2">
              <span class="text-teal-600 font-bold">&check;</span>
              <span>Reagent consumption tracking preventing inventory stockouts and expiry waste</span>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <!-- SECTION 8: OFFLINE-FIRST TECHNOLOGY ARCHITECTURE -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="bg-gradient-to-br from-slate-950 via-slate-900 to-teal-950 text-white rounded-3xl p-8 sm:p-12 lg:p-16 border border-slate-800 space-y-10">
        <div class="text-center max-w-3xl mx-auto space-y-3">
          <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-teal-500/10 text-teal-300 border border-teal-500/30">
            Technical Architecture
          </span>
          <h2 class="text-2xl sm:text-4xl font-extrabold tracking-tight">
            How Aarozi’s Offline-First LAN Topology Operates
          </h2>
          <p class="text-xs sm:text-sm text-slate-400">
            Complete understanding of where your data lives and why your lab never stops working.
          </p>
        </div>

        <!-- Architectural Visual Diagram -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
            <div class="w-12 h-12 rounded-xl bg-teal-500/20 text-teal-400 flex items-center justify-center mx-auto text-lg font-bold">
              1
            </div>
            <h3 class="text-sm font-bold text-white">Master Windows PC</h3>
            <p class="text-xs text-slate-400">
              Installed on your primary computer. Houses the local relational database, report engine, and cryptographic license verification service.
            </p>
          </div>

          <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
            <div class="w-12 h-12 rounded-xl bg-sky-500/20 text-sky-400 flex items-center justify-center mx-auto text-lg font-bold">
              2
            </div>
            <h3 class="text-sm font-bold text-white">Local LAN Router</h3>
            <p class="text-xs text-slate-400">
              Your existing clinic Wi-Fi or Ethernet switch. Broadcasts the LIS to all other clinic PCs with zero internet bandwidth consumption.
            </p>
          </div>

          <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
            <div class="w-12 h-12 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center mx-auto text-lg font-bold">
              3
            </div>
            <h3 class="text-sm font-bold text-white">LAN Workstations</h3>
            <p class="text-xs text-slate-400">
              Receptionists, phlebotomists, and pathologists connect via local browser (e.g. <code class="text-teal-300">http://192.168.1.100:8000</code>).
            </p>
          </div>
        </div>

        <div class="border-t border-slate-800 pt-6 text-center text-xs text-slate-400">
          <strong class="text-white">When is Internet Used?</strong> Only when customer-initiated: software version checks, WhatsApp PDF report dispatch via API, or customer-configured Google Drive encrypted backups.
        </div>
      </div>
    </section>

    <!-- SECTION 9: PRODUCT SCREENSHOTS & WORKFLOW (INTERACTIVE GALLERY) -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
      <div class="text-center max-w-3xl mx-auto space-y-3">
        <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300 border border-teal-200">
          Interactive Walkthrough
        </span>
        <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
          See the Diagnostic Workflow in Action
        </h2>
        <p class="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
          Explore how real patient registrations flow from front desk intake to authorized digital reports.
        </p>
      </div>

      <ScreenshotGallery />
    </section>

    <!-- SECTION 10: USE CASES & SOLUTIONS -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
      <div class="text-center max-w-3xl mx-auto space-y-3">
        <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
          Tailored for Every Diagnostic Facility
        </h2>
        <p class="text-sm text-slate-600 dark:text-slate-400">
          Whether you run a single collection point or a multi-department hospital transfusion centre.
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <NuxtLink
          v-for="uc in useCases"
          :key="uc.path"
          :to="uc.path"
          class="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-500 hover:shadow-lg transition-all space-y-3 group"
        >
          <span class="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300 border border-teal-200">
            {{ uc.tag }}
          </span>
          <h3 class="text-base font-bold text-slate-900 dark:text-white group-hover:text-teal-600 transition-colors">
            {{ uc.title }}
          </h3>
          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            {{ uc.desc }}
          </p>
          <span class="text-xs font-bold text-teal-600 inline-block pt-1 group-hover:underline">
            Read Solution Guide &rarr;
          </span>
        </NuxtLink>
      </div>
    </section>

    <!-- SECTION 11: REPORT FORMAT LIBRARY PREVIEW -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            Pre-Built NABL Diagnostic Report Formats
          </h2>
          <p class="text-xs text-slate-500 mt-1">
            Browse our library of pre-configured clinical templates across all diagnostic departments.
          </p>
        </div>
        <NuxtLink to="/report-formats">
          <Button variant="secondary" size="sm">
            Browse All 50+ Formats &rarr;
          </Button>
        </NuxtLink>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="rf in reportFormats"
          :key="rf.code"
          class="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2 hover:border-teal-400 transition-colors"
        >
          <div class="flex items-center justify-between text-[10px]">
            <span class="font-bold text-teal-600 uppercase">{{ rf.dept }}</span>
            <span class="font-mono text-slate-400">{{ rf.code }}</span>
          </div>
          <h3 class="text-xs font-bold text-slate-900 dark:text-white line-clamp-2">
            {{ rf.name }}
          </h3>
          <div class="text-[11px] text-slate-500 pt-1 flex items-center justify-between">
            <span>{{ rf.tests }} Parameters</span>
            <NuxtLink to="/report-formats" class="text-teal-600 hover:underline">Preview</NuxtLink>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 12: CUSTOMER CASE STUDIES & SUCCESS PROFILES -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="p-8 sm:p-12 rounded-3xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-8">
        <div class="text-center max-w-2xl mx-auto space-y-2">
          <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            Laboratory Modernization Case Studies
          </h2>
          <p class="text-xs text-slate-600 dark:text-slate-400">
            Real operational transformations achieved by diagnostic centers adopting Aarozi's offline-first architecture.
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 text-xs">
          <!-- Case Study 1 -->
          <div class="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
            <span class="px-2.5 py-1 rounded bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300 font-bold text-[10px]">
              PATHOLOGY LAB PROFILE &bull; MUMBAI, MH
            </span>
            <h3 class="text-sm font-bold text-slate-900 dark:text-white">
              Overcoming Frequent ISP Outages with Zero Revenue Loss
            </h3>
            <p class="text-slate-600 dark:text-slate-400 leading-relaxed">
              A standalone diagnostic center processing 180+ patients daily suffered recurring broadband cuts that stalled their cloud software for 2 to 3 hours every afternoon.
            </p>
            <div class="pt-2 border-t border-slate-100 dark:border-slate-800 grid grid-cols-3 gap-2 text-center">
              <div><strong class="text-sm text-teal-600 font-bold block">100%</strong> <span class="text-[10px] text-slate-500">Offline Uptime</span></div>
              <div><strong class="text-sm text-teal-600 font-bold block">45 Sec</strong> <span class="text-[10px] text-slate-500">Intake Time</span></div>
              <div><strong class="text-sm text-teal-600 font-bold block">0 Errors</strong> <span class="text-[10px] text-slate-500">Tube Mix-ups</span></div>
            </div>
          </div>

          <!-- Case Study 2 -->
          <div class="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
            <span class="px-2.5 py-1 rounded bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300 font-bold text-[10px]">
              BLOOD BANK & TRANSFUSION &bull; JAIPUR, RJ
            </span>
            <h3 class="text-sm font-bold text-slate-900 dark:text-white">
              Strict Donor Traceability & TTI Testing Compliance
            </h3>
            <p class="text-slate-600 dark:text-slate-400 leading-relaxed">
              Replacing paper donation records with Aarozi’s digital donor questionnaire, TTI marker validation, and cross-match reservation ledger.
            </p>
            <div class="pt-2 border-t border-slate-100 dark:border-slate-800 grid grid-cols-3 gap-2 text-center">
              <div><strong class="text-sm text-purple-600 font-bold block">Zero</strong> <span class="text-[10px] text-slate-500">Manual Logs</span></div>
              <div><strong class="text-sm text-purple-600 font-bold block">100%</strong> <span class="text-[10px] text-slate-500">Cold Chain Audit</span></div>
              <div><strong class="text-sm text-purple-600 font-bold block">ISO</strong> <span class="text-[10px] text-slate-500">Audit Ready</span></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 13: COMPARISON MATRIX -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
      <div class="text-center max-w-2xl mx-auto space-y-2">
        <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
          Why Diagnostic Centers Choose Aarozi
        </h2>
        <p class="text-xs text-slate-600 dark:text-slate-400">
          Comparing traditional manual or fragile cloud software against Aarozi’s offline-first engineering.
        </p>
      </div>

      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl overflow-hidden shadow-lg">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-50 dark:bg-slate-800/80 text-slate-500 uppercase text-[10px] font-bold">
            <tr>
              <th class="p-4 sm:p-5">Capability / Requirement</th>
              <th class="p-4 sm:p-5">Traditional Paper / Generic Softwares</th>
              <th class="p-4 sm:p-5 text-teal-600 dark:text-teal-400">Aarozi Healthcare LIS</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr>
              <td class="p-4 sm:p-5 font-bold text-slate-900 dark:text-white">Internet Outage Resilience</td>
              <td class="p-4 sm:p-5 text-slate-500">Fails entirely; laboratory stops operating</td>
              <td class="p-4 sm:p-5 text-emerald-600 font-bold">&check; 100% Operational without internet</td>
            </tr>
            <tr>
              <td class="p-4 sm:p-5 font-bold text-slate-900 dark:text-white">Patient Record Privacy</td>
              <td class="p-4 sm:p-5 text-slate-500">Stored on 3rd party public clouds or paper</td>
              <td class="p-4 sm:p-5 text-emerald-600 font-bold">&check; 100% Local Master PC Database</td>
            </tr>
            <tr>
              <td class="p-4 sm:p-5 font-bold text-slate-900 dark:text-white">Thermal Barcode Integration</td>
              <td class="p-4 sm:p-5 text-slate-500">Requires expensive third-party drivers</td>
              <td class="p-4 sm:p-5 text-emerald-600 font-bold">&check; Built-in Code 128 label generator</td>
            </tr>
            <tr>
              <td class="p-4 sm:p-5 font-bold text-slate-900 dark:text-white">Analyzer Interfacing</td>
              <td class="p-4 sm:p-5 text-slate-500">Manual re-typing of technician results</td>
              <td class="p-4 sm:p-5 text-emerald-600 font-bold">&check; Direct RS232 / TCP auto-import</td>
            </tr>
            <tr>
              <td class="p-4 sm:p-5 font-bold text-slate-900 dark:text-white">Licence Model</td>
              <td class="p-4 sm:p-5 text-slate-500">Mandatory monthly recurring fees forever</td>
              <td class="p-4 sm:p-5 text-emerald-600 font-bold">&check; Flexible Yearly or Lifetime Perpetual</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- SECTION 14: PRICING PREVIEW & INTERACTIVE CALCULATOR -->
    <section id="pricing" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
      <div class="text-center max-w-3xl mx-auto space-y-3">
        <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300 border border-teal-200">
          Transparent Pricing
        </span>
        <h2 class="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white">
          Straightforward Plans. No Hidden Charges.
        </h2>
        <p class="text-sm text-slate-600 dark:text-slate-400">
          Choose between an annual commercial subscription or a perpetual lifetime license. Both include offline-first operation, multi-PC LAN access, and full data ownership.
        </p>
      </div>

      <PricingCalculator />
    </section>

    <!-- SECTION 15: FREQUENTLY ASKED QUESTIONS -->
    <section id="faq" class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
      <div class="text-center space-y-2">
        <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
          Frequently Asked Questions
        </h2>
        <p class="text-xs text-slate-500">
          Clear answers regarding offline functionality, LAN installation, data privacy, and licensing.
        </p>
      </div>

      <div class="space-y-3 text-xs">
        <div
          v-for="(f, idx) in faqs"
          :key="idx"
          class="border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 overflow-hidden"
        >
          <button
            type="button"
            class="w-full p-4 sm:p-5 text-left font-bold text-slate-900 dark:text-white flex items-center justify-between gap-4 cursor-pointer"
            @click="toggleFaq(idx)"
          >
            <span>{{ f.q }}</span>
            <Icon name="chevron-down" size="xs" :class="{ 'rotate-180': activeFaq === idx }" class="transition-transform duration-200 shrink-0 text-slate-400" />
          </button>
          <div v-if="activeFaq === idx" class="px-4 sm:px-5 pb-5 text-slate-600 dark:text-slate-400 leading-relaxed border-t border-slate-100 dark:border-slate-800 pt-3">
            {{ f.a }}
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 16: FINAL CALL TO ACTION -->
    <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <CtaBanner
        title="Start Running Your Lab on Aarozi Healthcare Today"
        subtitle="Download the Windows installer or choose a commercial licence plan. 15-minute setup on your master PC with zero cloud dependency."
      />
    </section>
  </div>
</template>

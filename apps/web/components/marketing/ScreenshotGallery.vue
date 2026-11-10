<script setup lang="ts">
import { ref } from 'vue'
import Icon from '~/components/ui/Icon.vue'
import Badge from '~/components/ui/Badge.vue'

const activeWorkflow = ref('patient_intake')

const workflows = [
  {
    id: 'patient_intake',
    title: '1. Patient Intake & UHID',
    badge: 'Front-Office Desk',
    subtitle: 'Lightning-fast registration with Aadhaar / phone lookup, duplicate prevention, and urgent emergency toggle.',
    highlights: [
      'Automatic UHID generation (e.g. UHID-2026-0814)',
      'Real-time phonetic duplicate patient detection',
      'Referring doctor & hospital commission linkage',
      'Split payment collection (Cash, UPI, Card, Credit)',
    ],
    screenTitle: 'Patient Registration & Order Booking',
    screenSubtitle: 'Main Counter &bull; Workstation 01',
    mockDetails: {
      patient: 'Smt. Anjali Sharma, 38 Yrs / Female',
      tests: ['Complete Blood Count (CBC) with Automated Differential', 'Lipid Profile Comprehensive', 'Thyroid Stimulating Hormone (TSH)'],
      uhid: 'UHID-2026-04918',
      amount: '₹ 1,450.00 (PAID via UPI)',
    },
  },
  {
    id: 'barcode_sample',
    title: '2. Barcoding & Specimen Intake',
    badge: 'Phlebotomy Station',
    subtitle: 'Automated thermal barcode printing for vacutainers with color-coded tube guidance (EDTA, Serum, Fluoride).',
    highlights: [
      'One-click thermal printing to TSC / Zebra printers',
      'Specimen rejection workflow with clinical reason logging',
      'Precise sample collection timestamp audit',
      'Color-coded tube guide (Purple EDTA, Yellow SST, Grey Fluoride)',
    ],
    screenTitle: 'Specimen Barcoding & Phlebotomy Worklist',
    screenSubtitle: 'Sample Reception &bull; Workstation 02',
    mockDetails: {
      barcodes: ['SMP-202611-0081 (K2-EDTA)', 'SMP-202611-0082 (SST Gel)', 'SMP-202611-0083 (Fluoride)'],
      phlebo: 'Technician: R. Sharma (Phlebotomy Station A)',
      status: 'COLLECTED &bull; 11:42 AM',
    },
  },
  {
    id: 'results_entry',
    title: '3. Results & Automated Interfacing',
    badge: 'Laboratory Bench',
    subtitle: 'Rapid multi-parameter result entry with ASTM/HL7 analyzer bidirectional interfacing and abnormal flags.',
    highlights: [
      'Direct RS232 / TCP auto-fetch from Mindray, Cobas & Sysmex',
      'Automated calculations (e.g. Total/HDL ratio, eGFR, Absolute Neutrophil Count)',
      'Delta checks comparing against patient historical records',
      'Instant color-coded abnormal (High/Low) and Panic alerts',
    ],
    screenTitle: 'Pathology Result Entry & Delta Check Bench',
    screenSubtitle: 'Biochemistry & Hematology &bull; Workstation 03',
    mockDetails: {
      parameters: [
        { name: 'Hemoglobin (Hb)', val: '13.8 g/dL', normal: '12.0 - 15.5', flag: 'NORMAL' },
        { name: 'Fasting Blood Sugar', val: '168 mg/dL', normal: '70 - 100', flag: 'HIGH' },
        { name: 'Serum Creatinine', val: '0.9 mg/dL', normal: '0.6 - 1.2', flag: 'NORMAL' },
        { name: 'Platelet Count', val: '2.4 Lakhs/uL', normal: '1.5 - 4.5', flag: 'NORMAL' },
      ],
    },
  },
  {
    id: 'pathologist_approval',
    title: '4. Pathologist Review & Sign-Off',
    badge: 'Approval Desk',
    subtitle: 'Doctor verification station with tamper-evident audit trails, digital signatures, and re-run triggers.',
    highlights: [
      'Full longitudinal history comparison side-by-side',
      'One-click digital signature and QR-authenticated sign-off',
      'Optional re-test or sample recollection order trigger',
      'NABL-compliant pathologist sign-off audit log',
    ],
    screenTitle: 'Clinical Verification & Digital Authorization',
    screenSubtitle: 'Pathologist Room &bull; Workstation 04',
    mockDetails: {
      doctor: 'Dr. V. K. Raman, MD (Pathology) &bull; Reg: MCI-48912',
      action: 'Authorized & Digitally Signed',
      timestamp: 'Today at 02:15 PM',
    },
  },
  {
    id: 'report_delivery',
    title: '5. Tamper-Proof QR Diagnostic Report',
    badge: 'Delivery & WhatsApp',
    subtitle: 'High-resolution PDF reports formatted with custom lab letterheads, reference ranges, and verification QR code.',
    highlights: [
      'Cryptographically hashed QR code verifiable by smartphones',
      'Automated direct WhatsApp PDF report delivery via BYO API',
      'Department-wise pagination with custom lab header & footer',
      'Offline PDF generation in under 200 milliseconds',
    ],
    screenTitle: 'Diagnostic PDF Preview & QR Verification',
    screenSubtitle: 'Report Distribution Center &bull; Workstation 05',
    mockDetails: {
      pdfName: 'Report_UHID-2026-04918_CBC_LIPID.pdf',
      qrVerification: 'https://verify.aarozi.in/r/3f9a12bc',
      status: 'Ready for Print & Direct Dispatch',
    },
  },
]
</script>

<template>
  <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 lg:p-10 shadow-xl">
    <!-- Workflow Step Selector Tabs -->
    <div class="flex overflow-x-auto gap-2 pb-4 border-b border-slate-200 dark:border-slate-800">
      <button
        v-for="wf in workflows"
        :key="wf.id"
        type="button"
        class="px-4 py-2.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all flex items-center space-x-2 shrink-0 cursor-pointer"
        :class="[
          activeWorkflow === wf.id
            ? 'bg-teal-600 text-white shadow-md'
            : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
        ]"
        @click="activeWorkflow = wf.id"
      >
        <span>{{ wf.title }}</span>
      </button>
    </div>

    <!-- Active Step Content Area -->
    <div v-for="wf in workflows" :key="wf.id">
      <div v-if="activeWorkflow === wf.id" class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center pt-8">
        <!-- Left: Workflow Story & Highlights -->
        <div class="lg:col-span-5 space-y-4">
          <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-300 text-xs font-bold uppercase tracking-wider">
            <Icon name="check-circle" size="xs" />
            <span>{{ wf.badge }}</span>
          </div>

          <h3 class="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            {{ wf.title }}
          </h3>

          <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            {{ wf.subtitle }}
          </p>

          <ul class="space-y-2.5 pt-2">
            <li v-for="(h, idx) in wf.highlights" :key="idx" class="flex items-start space-x-2.5 text-xs text-slate-700 dark:text-slate-300 font-medium">
              <span class="w-4 h-4 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 mt-0.5 font-bold text-[10px]">
                &check;
              </span>
              <span>{{ h }}</span>
            </li>
          </ul>
        </div>

        <!-- Right: Authentic Interactive UI Mockup Card -->
        <div class="lg:col-span-7">
          <div class="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl font-mono text-xs text-slate-300">
            <!-- Simulated Window Top Bar -->
            <div class="bg-slate-900 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <span class="w-3 h-3 rounded-full bg-rose-500/80 inline-block" />
                <span class="w-3 h-3 rounded-full bg-amber-500/80 inline-block" />
                <span class="w-3 h-3 rounded-full bg-emerald-500/80 inline-block" />
                <span class="text-slate-400 text-[11px] font-sans font-semibold ml-2">Aarozi Healthcare LIS &bull; {{ wf.screenSubtitle }}</span>
              </div>
              <div class="text-[10px] text-teal-400 font-sans font-bold uppercase bg-teal-950/80 px-2 py-0.5 rounded border border-teal-800">
                LAN ONLINE
              </div>
            </div>

            <!-- Simulated Screen Body -->
            <div class="p-6 space-y-4 font-sans">
              <div class="flex items-center justify-between border-b border-slate-800/80 pb-3">
                <div>
                  <h4 class="font-bold text-sm text-white">{{ wf.screenTitle }}</h4>
                  <p class="text-[11px] text-slate-400">Master Laboratory Database (Local SQLite / PostgreSQL)</p>
                </div>
                <span class="text-emerald-400 font-bold text-xs bg-emerald-950/60 px-2.5 py-1 rounded-md border border-emerald-800">
                  Zero Network Latency
                </span>
              </div>

              <!-- Dynamic Mock Content based on workflow -->
              <div v-if="wf.id === 'patient_intake'" class="space-y-3 text-xs">
                <div class="bg-slate-900/90 p-3 rounded-xl border border-slate-800 grid grid-cols-2 gap-3">
                  <div><span class="text-slate-500 block text-[10px]">PATIENT NAME:</span> <strong class="text-white">{{ wf.mockDetails.patient }}</strong></div>
                  <div><span class="text-slate-500 block text-[10px]">GENERATED UHID:</span> <strong class="text-teal-400 font-mono">{{ wf.mockDetails.uhid }}</strong></div>
                </div>
                <div class="bg-slate-900/90 p-3 rounded-xl border border-slate-800 space-y-1.5">
                  <span class="text-slate-500 block text-[10px]">ORDERED INVESTIGATIONS:</span>
                  <div v-for="t in wf.mockDetails.tests" :key="t" class="flex items-center space-x-2 text-slate-200">
                    <span class="w-1.5 h-1.5 rounded-full bg-teal-400" />
                    <span>{{ t }}</span>
                  </div>
                </div>
                <div class="flex items-center justify-between text-xs pt-1">
                  <span class="text-slate-400">Total Billed: <strong class="text-white">{{ wf.mockDetails.amount }}</strong></span>
                  <span class="text-emerald-400 font-bold">&check; Barcode Printed Automatically</span>
                </div>
              </div>

              <div v-else-if="wf.id === 'barcode_sample'" class="space-y-3 text-xs">
                <div class="bg-slate-900/90 p-3 rounded-xl border border-slate-800 space-y-2">
                  <span class="text-slate-500 block text-[10px]">GENERATED TUBE LABELS (CODE 128 THERMAL):</span>
                  <div v-for="b in wf.mockDetails.barcodes" :key="b" class="flex items-center justify-between bg-slate-950 p-2 rounded-lg border border-slate-800">
                    <span class="font-mono text-teal-300 font-bold">{{ b }}</span>
                    <span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">PRINTED</span>
                  </div>
                </div>
                <div class="flex items-center justify-between text-xs text-slate-400">
                  <span>{{ wf.mockDetails.phlebo }}</span>
                  <span class="text-emerald-400 font-bold">{{ wf.mockDetails.status }}</span>
                </div>
              </div>

              <div v-else-if="wf.id === 'results_entry'" class="space-y-2 text-xs">
                <div class="bg-slate-900/90 rounded-xl border border-slate-800 overflow-hidden">
                  <table class="w-full text-left">
                    <thead class="bg-slate-800/80 text-[10px] uppercase text-slate-400">
                      <tr>
                        <th class="p-2.5">Parameter</th>
                        <th class="p-2.5">Result</th>
                        <th class="p-2.5">Normal Interval</th>
                        <th class="p-2.5">Status</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800 text-xs">
                      <tr v-for="param in wf.mockDetails.parameters" :key="param.name" class="hover:bg-slate-800/40">
                        <td class="p-2.5 font-medium text-white">{{ param.name }}</td>
                        <td class="p-2.5 font-bold font-mono" :class="param.flag === 'HIGH' ? 'text-rose-400' : 'text-slate-200'">{{ param.val }}</td>
                        <td class="p-2.5 text-slate-400 font-mono text-[11px]">{{ param.normal }}</td>
                        <td class="p-2.5">
                          <span
                            class="px-2 py-0.5 rounded text-[10px] font-bold"
                            :class="param.flag === 'HIGH' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-emerald-950 text-emerald-300 border border-emerald-800'"
                          >
                            {{ param.flag }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div v-else-if="wf.id === 'pathologist_approval'" class="space-y-3 text-xs">
                <div class="bg-slate-900/90 p-4 rounded-xl border border-slate-800 space-y-2 text-center">
                  <div class="w-12 h-12 rounded-full bg-teal-500/20 text-teal-400 flex items-center justify-center mx-auto text-xl font-bold">
                    &check;
                  </div>
                  <h5 class="text-white font-bold text-sm">{{ wf.mockDetails.action }}</h5>
                  <p class="text-slate-400 text-xs">{{ wf.mockDetails.doctor }}</p>
                  <p class="text-[11px] text-teal-400 font-mono">{{ wf.mockDetails.timestamp }} &bull; Ed25519 Sign-Off Attached</p>
                </div>
              </div>

              <div v-else-if="wf.id === 'report_delivery'" class="space-y-3 text-xs">
                <div class="bg-slate-900/90 p-4 rounded-xl border border-slate-800 space-y-3">
                  <div class="flex items-center justify-between">
                    <span class="text-slate-400">PDF File: <strong class="text-white">{{ wf.mockDetails.pdfName }}</strong></span>
                    <span class="text-teal-400 font-mono text-[10px]">210 KB &bull; Fast Render</span>
                  </div>
                  <div class="bg-slate-950 p-3 rounded-lg border border-slate-800 flex items-center justify-between">
                    <div>
                      <div class="text-[10px] text-slate-500 uppercase font-bold">Encrypted Verification Link</div>
                      <div class="text-xs text-teal-300 font-mono">{{ wf.mockDetails.qrVerification }}</div>
                    </div>
                    <span class="px-2.5 py-1 rounded bg-teal-900/60 text-teal-300 font-bold text-[10px] border border-teal-700">
                      QR ACTIVE
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


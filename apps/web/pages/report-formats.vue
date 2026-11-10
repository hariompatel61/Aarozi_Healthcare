<script setup lang="ts">
import { ref, computed } from 'vue'
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const selectedDept = ref('all')
const selectedReport = ref<any>(null)
const withLetterhead = ref(true)

const departments = [
  { id: 'all', label: 'All Formats' },
  { id: 'hematology', label: 'Hematology' },
  { id: 'biochemistry', label: 'Biochemistry' },
  { id: 'clinical_path', label: 'Clinical Path' },
  { id: 'serology', label: 'Serology' },
  { id: 'radiology', label: 'Radiology & USG' },
]

const reportTemplates = [
  {
    id: 'cbc',
    dept: 'hematology',
    title: 'Complete Blood Count (CBC with 5-Part Differential)',
    description: 'NABL-compliant format with 22 hematological parameters, age-specific reference ranges, and graphical flags.',
    parameters: [
      { name: 'Hemoglobin (Hb)', result: '14.2', unit: 'g/dL', normal: '13.0 - 17.0', status: 'Normal' },
      { name: 'Total Leukocyte Count (TLC)', result: '11,400', unit: '/cumm', normal: '4,000 - 10,000', status: 'High' },
      { name: 'RBC Count', result: '4.85', unit: 'mil/cumm', normal: '4.50 - 5.50', status: 'Normal' },
      { name: 'Platelet Count', result: '2.10', unit: 'lakh/cumm', normal: '1.50 - 4.50', status: 'Normal' },
      { name: 'Neutrophils', result: '72', unit: '%', normal: '40 - 75', status: 'Normal' },
      { name: 'Lymphocytes', result: '22', unit: '%', normal: '20 - 45', status: 'Normal' },
    ],
  },
  {
    id: 'lft',
    dept: 'biochemistry',
    title: 'Liver Function Test (LFT Profile)',
    description: 'Enzyme and protein analysis including Bilirubin total/direct, SGOT, SGPT, Alkaline Phosphatase, and Albumin/Globulin ratio.',
    parameters: [
      { name: 'Total Bilirubin', result: '0.8', unit: 'mg/dL', normal: '0.2 - 1.2', status: 'Normal' },
      { name: 'Direct Bilirubin', result: '0.2', unit: 'mg/dL', normal: '0.0 - 0.3', status: 'Normal' },
      { name: 'SGOT (AST)', result: '32', unit: 'U/L', normal: '10 - 40', status: 'Normal' },
      { name: 'SGPT (ALT)', result: '38', unit: 'U/L', normal: '10 - 45', status: 'Normal' },
      { name: 'Serum Alkaline Phosphatase', result: '88', unit: 'U/L', normal: '40 - 129', status: 'Normal' },
      { name: 'Total Protein', result: '7.1', unit: 'g/dL', normal: '6.4 - 8.3', status: 'Normal' },
    ],
  },
  {
    id: 'kft',
    dept: 'biochemistry',
    title: 'Kidney Function Test (KFT / RFT)',
    description: 'Renal panel evaluating Blood Urea, Serum Creatinine, Uric Acid, eGFR, and Serum Electrolytes (Na+, K+, Cl-).',
    parameters: [
      { name: 'Blood Urea', result: '28', unit: 'mg/dL', normal: '15 - 40', status: 'Normal' },
      { name: 'Serum Creatinine', result: '0.95', unit: 'mg/dL', normal: '0.70 - 1.30', status: 'Normal' },
      { name: 'Serum Uric Acid', result: '5.4', unit: 'mg/dL', normal: '3.5 - 7.2', status: 'Normal' },
      { name: 'Estimated GFR (CKD-EPI)', result: '> 90', unit: 'mL/min/1.73m²', normal: '> 90', status: 'Normal' },
      { name: 'Sodium (Na+)', result: '139', unit: 'mmol/L', normal: '135 - 145', status: 'Normal' },
      { name: 'Potassium (K+)', result: '4.2', unit: 'mmol/L', normal: '3.5 - 5.1', status: 'Normal' },
    ],
  },
  {
    id: 'lipid',
    dept: 'biochemistry',
    title: 'Lipid Profile (Coronary Risk Assessment)',
    description: 'Cardiovascular screening panel including Total Cholesterol, Triglycerides, HDL, LDL, VLDL, and non-HDL Cholesterol.',
    parameters: [
      { name: 'Total Cholesterol', result: '178', unit: 'mg/dL', normal: '< 200', status: 'Desirable' },
      { name: 'Serum Triglycerides', result: '142', unit: 'mg/dL', normal: '< 150', status: 'Normal' },
      { name: 'HDL Cholesterol (Good)', result: '48', unit: 'mg/dL', normal: '> 40', status: 'Optimal' },
      { name: 'LDL Cholesterol (Bad)', result: '101', unit: 'mg/dL', normal: '< 100', status: 'Borderline' },
      { name: 'Chol / HDL Ratio', result: '3.7', unit: 'ratio', normal: '< 4.5', status: 'Normal' },
    ],
  },
  {
    id: 'thyroid',
    dept: 'serology',
    title: 'Thyroid Function Test (T3, T4, TSH Ultra)',
    description: 'Endocrine hormonal evaluation utilizing ultra-sensitive chemiluminescence assay ranges.',
    parameters: [
      { name: 'Total Triiodothyronine (T3)', result: '1.24', unit: 'ng/mL', normal: '0.80 - 2.00', status: 'Normal' },
      { name: 'Total Thyroxine (T4)', result: '7.8', unit: 'µg/dL', normal: '5.1 - 14.1', status: 'Normal' },
      { name: 'TSH (Ultrasensitive)', result: '2.45', unit: 'µIU/mL', normal: '0.40 - 4.20', status: 'Normal' },
    ],
  },
  {
    id: 'urine',
    dept: 'clinical_path',
    title: 'Urine Routine & Microscopic Examination',
    description: 'Physical, chemical dipstick, and microscopic sediment evaluation with automated abnormal highlighting.',
    parameters: [
      { name: 'Color / Transparency', result: 'Pale Yellow / Clear', unit: '', normal: 'Pale Yellow / Clear', status: 'Normal' },
      { name: 'Reaction (pH)', result: '6.0', unit: '', normal: '4.8 - 7.5', status: 'Normal' },
      { name: 'Protein (Albumin)', result: 'Nil', unit: '', normal: 'Nil', status: 'Normal' },
      { name: 'Sugar (Glucose)', result: 'Nil', unit: '', normal: 'Nil', status: 'Normal' },
      { name: 'Pus Cells (WBCs)', result: '1 - 2', unit: '/hpf', normal: '0 - 5', status: 'Normal' },
      { name: 'RBCs', result: 'Nil', unit: '/hpf', normal: 'Nil', status: 'Normal' },
    ],
  },
  {
    id: 'usg_abdomen',
    dept: 'radiology',
    title: 'Ultrasound Whole Abdomen & Pelvis',
    description: 'Structured sonography report covering Liver, Gallbladder, Pancreas, Spleen, Kidneys, and Urinary Bladder.',
    parameters: [
      { name: 'Liver', result: 'Normal in size (13.8 cm). Normal echotexture. No focal mass lesion.', unit: '', normal: 'Normal', status: 'Normal' },
      { name: 'Gallbladder', result: 'Physiologically distended. Walls normal. No calculus or sludge.', unit: '', normal: 'Normal', status: 'Normal' },
      { name: 'Kidneys', result: 'Both kidneys normal size, shape, and cortical thickness. No hydronephrosis.', unit: '', normal: 'Normal', status: 'Normal' },
      { name: 'Urinary Bladder', result: 'Adequately distended. Lumen free of intraluminal mass or calculus.', unit: '', normal: 'Normal', status: 'Normal' },
      { name: 'Impression', result: 'Normal study of whole abdomen and pelvis.', unit: '', normal: '', status: 'Normal' },
    ],
  },
]

const filteredTemplates = computed(() => {
  if (selectedDept.value === 'all') return reportTemplates
  return reportTemplates.filter((t) => t.dept === selectedDept.value)
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="file-text" size="xs" />
        <span>NABL & ISO Format Catalog</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Print-Ready Clinical Report Formats
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Explore laboratory and radiology report designs optimized for single-page compaction, doctor digital signatures, and tamper-evident QR verification.
      </p>
    </div>

    <!-- Filter Buttons -->
    <div class="flex flex-wrap items-center justify-center gap-2">
      <button
        v-for="dept in departments"
        :key="dept.id"
        @click="selectedDept = dept.id"
        class="px-4 py-2 rounded-xl text-xs font-bold transition-all"
        :class="selectedDept === dept.id ? 'bg-teal-600 text-white shadow-md' : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:border-teal-500'"
      >
        {{ dept.label }}
      </button>
    </div>

    <!-- Reports Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="item in filteredTemplates"
        :key="item.id"
        class="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 flex flex-col justify-between hover:shadow-lg transition-all"
      >
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
              {{ item.dept }}
            </span>
            <span class="text-[10px] font-bold text-teal-600 flex items-center space-x-1">
              <Icon name="qr-code" size="xs" />
              <span>QR Verified</span>
            </span>
          </div>
          <h3 class="text-base font-bold text-slate-900 dark:text-white">{{ item.title }}</h3>
          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{{ item.description }}</p>

          <!-- Sample Parameters Preview Table -->
          <div class="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-1.5 text-[11px]">
            <div v-for="p in item.parameters.slice(0, 3)" :key="p.name" class="flex justify-between items-center text-slate-700 dark:text-slate-300">
              <span class="truncate pr-2 text-slate-600 dark:text-slate-400">{{ p.name }}</span>
              <span class="font-bold text-slate-900 dark:text-white">{{ p.result }} {{ p.unit }}</span>
            </div>
          </div>
        </div>

        <div class="pt-6 mt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <button
            @click="selectedReport = item"
            class="text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline flex items-center space-x-1"
          >
            <span>Live Interactive Preview</span>
            <Icon name="chevron-right" size="xs" />
          </button>
          <span class="text-[11px] text-slate-400">A4 / Letter</span>
        </div>
      </div>
    </div>

    <!-- Live Preview Modal -->
    <div
      v-if="selectedReport"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm"
      @click.self="selectedReport = null"
    >
      <div class="w-full max-w-3xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl p-6 sm:p-8 space-y-6 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h3 class="text-lg font-bold text-slate-900 dark:text-white">{{ selectedReport.title }}</h3>
            <p class="text-xs text-slate-500">Preview simulated A4 report with cryptographic signature and QR header</p>
          </div>
          <button
            @click="selectedReport = null"
            class="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center justify-center font-bold hover:bg-slate-200"
          >
            ✕
          </button>
        </div>

        <!-- Simulated Report Sheet -->
        <div class="border border-slate-200 dark:border-slate-800 rounded-2xl p-6 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white space-y-6 text-xs shadow-inner">
          <!-- Letterhead -->
          <div class="flex items-center justify-between border-b pb-4 border-slate-300 dark:border-slate-800">
            <div>
              <h2 class="text-base font-black text-teal-600">AAROZI ADVANCED DIAGNOSTICS</h2>
              <p class="text-[10px] text-slate-500">ISO 15189:2022 Accredited | NABL Registration: M-9821</p>
              <p class="text-[10px] text-slate-500">42 Healthcare Avenue, Medical District. Phone: +91 98765 43210</p>
            </div>
            <div class="text-right">
              <div class="w-14 h-14 bg-slate-900 text-white rounded-lg flex items-center justify-center text-[9px] font-mono p-1 text-center border">
                QR CODE VERIFIED
              </div>
            </div>
          </div>

          <!-- Patient Demographics Header -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
            <div><span class="text-slate-400 block text-[10px]">Patient Name:</span><strong>Mrs. Sunita Verma</strong></div>
            <div><span class="text-slate-400 block text-[10px]">Age / Sex:</span><strong>45 Y / Female</strong></div>
            <div><span class="text-slate-400 block text-[10px]">UHID / Sample ID:</span><span class="font-mono font-bold text-teal-600">AH-2026-9021</span></div>
            <div><span class="text-slate-400 block text-[10px]">Ref Doctor:</span><strong>Dr. R. K. Sharma (MD)</strong></div>
          </div>

          <!-- Test Results Table -->
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead>
                <tr class="border-b border-slate-300 dark:border-slate-800 text-[10px] font-bold uppercase text-slate-500">
                  <th class="py-2">Investigation</th>
                  <th class="py-2">Observed Value</th>
                  <th class="py-2">Biological Reference</th>
                  <th class="py-2">Unit</th>
                  <th class="py-2 text-right">Interpretation</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200 dark:divide-slate-800/60">
                <tr v-for="param in selectedReport.parameters" :key="param.name" class="py-2">
                  <td class="py-2 font-medium">{{ param.name }}</td>
                  <td class="py-2 font-bold" :class="param.status === 'High' ? 'text-red-600' : 'text-slate-900 dark:text-white'">{{ param.result }}</td>
                  <td class="py-2 text-slate-500">{{ param.normal || '—' }}</td>
                  <td class="py-2 text-slate-500">{{ param.unit || '—' }}</td>
                  <td class="py-2 text-right">
                    <span
                      class="px-2 py-0.5 rounded text-[10px] font-bold"
                      :class="param.status === 'High' ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'"
                    >
                      {{ param.status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Doctor Signature Block -->
          <div class="pt-6 border-t border-slate-300 dark:border-slate-800 flex justify-between items-end text-[10px]">
            <div class="text-slate-500">
              <p>Sample Collected: 10-Nov-2026 08:30 AM</p>
              <p>Report Released: 10-Nov-2026 11:15 AM</p>
              <p class="font-mono text-[9px] text-teal-600">ED25519-SIG: 9f8a...33cd-VERIFIED</p>
            </div>
            <div class="text-right space-y-1">
              <div class="italic font-serif text-slate-700 dark:text-slate-300 text-sm">Dr. A. Sen, MD</div>
              <p class="font-bold text-slate-900 dark:text-white">Consultant Pathologist</p>
              <p class="text-slate-400">Reg No: WB-MC-49210</p>
            </div>
          </div>
        </div>

        <div class="flex justify-end space-x-3">
          <Button variant="secondary" size="sm" @click="selectedReport = null">Close Preview</Button>
          <NuxtLink to="/download">
            <Button variant="primary" size="sm">Download Software to Test</Button>
          </NuxtLink>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

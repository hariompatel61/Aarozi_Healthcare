<script setup lang="ts">
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const caseStudies = [
  {
    labName: 'Apex Diagnostic & Imaging Centre',
    location: 'Lucknow, Uttar Pradesh',
    metrics: [
      { label: 'TAT Reduction', value: '55%' },
      { label: 'Daily Workload', value: '450+ patients' },
      { label: 'LAN Desks', value: '8 concurrent' },
    ],
    headline: 'Eliminated morning counter chaos and slashed turnaround time from 6 hours to 2.5 hours',
    story: 'Apex previously used a sluggish cloud LIS that frequently stalled during peak fasting hours due to broadband flakiness. Switching to Aarozi LAN Hub enabled instantaneous registration, automated split-tube barcoding, and zero-downtime operation.',
    quote: 'Our receptionists register patients in under 45 seconds now. Even when our internet went down for two days during road digging, our lab operated at 100% capacity without losing a single test record.',
    author: 'Dr. Vivek Saxena, Managing Director',
  },
  {
    labName: 'Shree Krishna Clinical Pathology',
    location: 'Surat, Gujarat',
    metrics: [
      { label: 'Annual SaaS Savings', value: '₹95,000+' },
      { label: 'Barcode Accuracy', value: '100%' },
      { label: 'Audit Compliance', value: 'NABL Ready' },
    ],
    headline: 'From recurring monthly SaaS extortion to perpetual software ownership',
    story: 'Paying ₹8,000 per month for a cloud software that throttled report PDF downloads prompted Shree Krishna Lab to evaluate Aarozi. Deploying the Lifetime Enterprise license eliminated annual SaaS subscriptions and brought all patient data safely onto their local server.',
    quote: 'The cryptographic QR report format won our referring doctors trust. They scan the QR code with their mobile phone and immediately verify our signature and test results.',
    author: 'Dr. P. N. Patel, Chief Pathologist',
  },
  {
    labName: 'CarePlus Multispeciality & Blood Centre',
    location: 'Patna, Bihar',
    metrics: [
      { label: 'Blood Bag Traceability', value: '100%' },
      { label: 'TTI Safety Checks', value: 'Zero Overrides' },
      { label: 'Cold-Chain Audits', value: 'Automated' },
    ],
    headline: 'Seamless integration of routine hematology with blood bank component separation',
    story: 'Managing emergency blood transfusions alongside high-volume routine diagnostics required an airtight system. Aarozi unified their donor registry, cross-matching bench, and clinical reporting under one database.',
    quote: 'The automated deferral registry and expiry sentinel prevents human error before blood components leave the cold chain.',
    author: 'Dr. Archana Roy, Head of Transfusion Medicine',
  },
]
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="award" size="xs" />
        <span>Verified Outcomes</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Trusted by Modern Diagnostic Laboratories Across India
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Discover how standalone pathology labs and integrated diagnostic centers achieve operational speed, absolute data privacy, and zero software downtime with Aarozi.
      </p>
    </div>

    <!-- Case Studies List -->
    <div class="space-y-10">
      <div
        v-for="study in caseStudies"
        :key="study.labName"
        class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 sm:p-10 shadow-sm space-y-6"
      >
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-6">
          <div>
            <h3 class="text-xl font-bold text-slate-900 dark:text-white">{{ study.labName }}</h3>
            <p class="text-xs text-teal-600 dark:text-teal-400 font-semibold flex items-center space-x-1 mt-1">
              <Icon name="map-pin" size="xs" />
              <span>{{ study.location }}</span>
            </p>
          </div>
          <!-- Metrics -->
          <div class="flex items-center space-x-6">
            <div v-for="m in study.metrics" :key="m.label" class="text-center">
              <div class="text-lg sm:text-2xl font-black text-slate-900 dark:text-white">{{ m.value }}</div>
              <div class="text-[10px] text-slate-500 font-medium uppercase tracking-wider">{{ m.label }}</div>
            </div>
          </div>
        </div>

        <div class="space-y-3">
          <h4 class="text-base font-bold text-slate-900 dark:text-white">{{ study.headline }}</h4>
          <p class="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{{ study.story }}</p>
        </div>

        <div class="rounded-2xl bg-slate-50 dark:bg-slate-800/50 p-5 border-l-4 border-teal-500 space-y-2">
          <p class="text-xs sm:text-sm italic text-slate-700 dark:text-slate-300">“{{ study.quote }}”</p>
          <p class="text-[11px] font-bold text-slate-900 dark:text-white">— {{ study.author }}</p>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


<script setup lang="ts">
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="layers" size="xs" />
        <span>Unified Solution</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        All-in-One LIS + RIS for Integrated Diagnostic Centres
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Combine Pathology, Radiology, Ultrasound, ECG, and Cardiology into a single unified front-desk invoice, single patient UHID, and merged report delivery workflow.
      </p>
    </div>

    <!-- Features specific to Integrated Centres -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="credit-card" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Unified POS Cashier Desk</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Order a Complete Blood Count (Pathology), Chest X-Ray (Radiology), and Whole Abdomen Ultrasound on a single bill with split payment support (Cash + UPI).
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
          <Icon name="users" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Cross-Department Routing</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Automatic worklist segregation: blood samples route to phlebotomy and the laboratory analyzer benches, while imaging procedures queue in radiology worklists.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="shield-check" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Unified Patient Delivery</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Deliver one merged master PDF or separate department-wise reports. Patients access everything with a single QR code scan or SMS link.
        </p>
      </div>
    </div>

    <!-- Comparative Advantage -->
    <div class="p-8 sm:p-12 rounded-3xl bg-slate-900 text-white border border-slate-800 space-y-6">
      <div class="max-w-3xl space-y-3">
        <h2 class="text-2xl font-bold tracking-tight">Stop Juggling Two Different Software Systems</h2>
        <p class="text-xs sm:text-sm text-slate-400 leading-relaxed">
          Traditional centres buy one LIS for pathology and another standalone RIS software for ultrasound/X-ray, forcing staff to register patients twice and print mismatched receipts. Aarozi brings complete clinical unity.
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs pt-4 border-t border-slate-800">
        <div><strong class="text-teal-400 block mb-1">Single Doctor Referral Commission</strong><span>Calculate combined referral incentives for pathology + imaging seamlessly.</span></div>
        <div><strong class="text-teal-400 block mb-1">Consolidated Daily Cash Balance</strong><span>One end-of-day revenue reconciliation across all cashiers and counters.</span></div>
        <div><strong class="text-teal-400 block mb-1">Health Checkup Packages</strong><span>Design comprehensive executive health packages covering blood, urine, ECG, and X-ray.</span></div>
        <div><strong class="text-teal-400 block mb-1">LAN Workstation Scaling</strong><span>Reception, sample lab, and radiology report rooms work simultaneously.</span></div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


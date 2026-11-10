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
        <Icon name="activity" size="xs" />
        <span>Specialized Solution</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Tailored for Standalone & Multi-Branch Pathology Laboratories
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        From fasting blood draws to NABL-standard verified reports: streamline technician worklists, auto-calculate derived ratios, flag critical panic values, and deliver tamper-evident QR reports.
      </p>
    </div>

    <!-- Features specific to Pathology -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="check-circle" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Sample Accessioning & Barcoding</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Automatic split-tube barcode printing (EDTA Purple, Serum Red, Fluoride Grey). Eliminates sample mix-up and guarantees pre-analytical traceability.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
          <Icon name="alert-triangle" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Abnormal & Critical Panic Alerts</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Age- and gender-specific reference ranges. High/Low values highlighted in bold red. Critical panic alerts surface immediately for urgent clinical escalation.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="file-text" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Pathologist Verification & Signing</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Two-pane approval desk with previous patient history comparison. Apply secure digital doctor signatures with one click before automated release.
        </p>
      </div>
    </div>

    <!-- Supported Departments -->
    <div class="p-8 sm:p-12 rounded-3xl bg-slate-900 text-white border border-slate-800 space-y-6">
      <h2 class="text-2xl font-bold tracking-tight">Full Department Coverage Out-of-the-Box</h2>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-center">
        <div class="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/60">
          <span class="text-teal-400 font-bold block text-sm">Hematology</span>
          <span class="text-[11px] text-slate-400">CBC, ESR, Peripheral Smear</span>
        </div>
        <div class="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/60">
          <span class="text-teal-400 font-bold block text-sm">Biochemistry</span>
          <span class="text-[11px] text-slate-400">LFT, KFT, Lipid, HbA1c</span>
        </div>
        <div class="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/60">
          <span class="text-teal-400 font-bold block text-sm">Clinical Path</span>
          <span class="text-[11px] text-slate-400">Urine R/M, Stool, Semen</span>
        </div>
        <div class="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/60">
          <span class="text-teal-400 font-bold block text-sm">Serology</span>
          <span class="text-[11px] text-slate-400">Widal, Dengue, HIV, HBsAg</span>
        </div>
        <div class="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/60">
          <span class="text-teal-400 font-bold block text-sm">Microbiology</span>
          <span class="text-[11px] text-slate-400">Culture & Sensitivity (AST)</span>
        </div>
        <div class="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/60">
          <span class="text-teal-400 font-bold block text-sm">Histopathology</span>
          <span class="text-[11px] text-slate-400">Biopsy, Gross & Microscopic</span>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

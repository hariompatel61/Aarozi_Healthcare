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
      <NuxtLink to="/features" class="inline-flex items-center space-x-1.5 text-xs font-bold text-teal-600 hover:underline">
        <Icon name="arrow-left" size="xs" />
        <span>All Features</span>
      </NuxtLink>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Laboratory Reporting & Verification Engine
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        NABL-aligned clinical reporting with age/gender-specific intervals, automated calculations, panic value warnings, and digital pathologist authorization.
      </p>
    </div>

    <!-- Core Capabilities Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="adjustments" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Multi-Tier Reference Ranges</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Configure exact biological reference intervals segmented by gender (Male/Female/Other) and precise age brackets (Neonatal 0-30 days, Pediatric 1-12 yrs, Adult, Geriatric).
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-rose-100 dark:bg-rose-950 text-rose-600 dark:text-rose-400 flex items-center justify-center font-bold">
          <Icon name="exclamation" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Abnormal & Panic Alerts</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Results falling outside standard biological limits are automatically flagged with high/low visual badges. Critical panic thresholds trigger immediate doctor alerts.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="badge-check" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Digital Signatures & Seal</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Attach authenticated pathologist and laboratory director digital signature images, medical council registration numbers, and institutional stamps on authorized reports.
        </p>
      </div>
    </div>

    <!-- Department-Wise Reporting Section -->
    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 sm:p-12 shadow-lg space-y-6">
      <h2 class="text-2xl font-bold text-slate-900 dark:text-white">
        Standardized Across All Diagnostic Disciplines
      </h2>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
        <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
          <strong class="text-teal-600 block font-bold mb-1">Hematology</strong>
          <span class="text-slate-500">CBC, ESR, Peripheral Smear, Coagulation PT/INR, Hemoglobin Electrophoresis.</span>
        </div>
        <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
          <strong class="text-teal-600 block font-bold mb-1">Biochemistry</strong>
          <span class="text-slate-500">LFT, KFT, Lipid Profile, Electrolytes, Cardiac Enzymes, HbA1c Glycated Hemoglobin.</span>
        </div>
        <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
          <strong class="text-teal-600 block font-bold mb-1">Immunology & Serology</strong>
          <span class="text-slate-500">Thyroid Profile, Vitamin D & B12, Viral Markers (HIV, HBsAg, HCV), CRP Quantitative.</span>
        </div>
        <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
          <strong class="text-teal-600 block font-bold mb-1">Clinical Pathology</strong>
          <span class="text-slate-500">Urine Routine & Microscopic, Stool Occult Blood, Semen Analysis, Body Fluid Cytology.</span>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

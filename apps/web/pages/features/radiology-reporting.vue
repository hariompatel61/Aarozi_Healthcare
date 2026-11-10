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
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <NuxtLink to="/features" class="inline-flex items-center space-x-1.5 text-xs font-bold text-teal-600 hover:underline">
        <Icon name="arrow-left" size="xs" />
        <span>All Features</span>
      </NuxtLink>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Radiology & Ultrasound Reporting
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Structured impression templates and narrative findings for Ultrasound, X-Ray, CT, MRI, and 12-lead ECG investigations.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="document" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Structured Macro Templates</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          One-click macros for normal Whole Abdomen USG, Chest PA View, KUB, Obstetric growth scans, and Pelvic imaging. Radiologists only customize abnormal findings.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
          <Icon name="clipboard" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Organ-Wise Checklist</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Systematic assessment of Liver, Gallbladder, Pancreas, Spleen, Kidneys, and Urinary Bladder ensures comprehensive diagnostic reporting with zero missed observations.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-950 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
          <Icon name="check-circle" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Unified Patient File</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Combine blood pathology reports and ultrasound imaging findings onto a single consolidated patient summary sheet and billing invoice.
        </p>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


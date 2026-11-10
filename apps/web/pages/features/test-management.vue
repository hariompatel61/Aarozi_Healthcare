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
        Test Catalog & Automated Calculations
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Over 500+ pre-seeded clinical parameters, multi-test profiles, mathematical formula derivation, and outsourced referral tracking.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="calculator" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Real-Time Formula Engine</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Define mathematical expressions such as <code>Total_Cholesterol / HDL</code>, <code>Total_Bilirubin - Direct_Bilirubin</code>, or CKD-EPI eGFR. Calculates instantly during result entry.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
          <Icon name="cube" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Flexible Health Checkup Packages</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Bundle individual blood tests into promotional profiles (e.g. Master Health Checkup, Executive Diabetes Screen, Antenatal Profile) with custom promotional pricing.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-950 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
          <Icon name="truck" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Outsourced Test Dispatch</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          For specialized genetic or histopathology tests sent to reference laboratories (Dr. Lal, Metropolis, SRL, etc.), track courier dispatch, B2B cost price, and incoming report imports.
        </p>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


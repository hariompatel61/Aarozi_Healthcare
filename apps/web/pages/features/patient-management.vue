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
        Patient Management & Unique Health ID (UHID)
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Accelerate reception intake, eliminate duplicate patient records, and maintain longitudinal clinical histories across all lifetime visits.
      </p>
    </div>

    <!-- Core Capabilities Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="search" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Smart Phone & Demographics Lookup</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Typing a mobile number or name immediately surfaces existing patient profiles. Auto-populates age, gender, address, and primary physician in under 3 seconds.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
          <Icon name="shield" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Duplicate Detection & Merge</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Intelligent phonetic algorithms detect near-identical names or alternate contact numbers. Receptionists can merge duplicate entries while preserving previous orders.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="clock" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Longitudinal Visit History</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Every past visit, ordered test, payment invoice, and verified report is permanently organized under the patient’s permanent UHID for instant recall.
        </p>
      </div>
    </div>

    <!-- Workflow Detail Card -->
    <div class="p-8 sm:p-12 rounded-3xl bg-slate-900 text-white border border-slate-800 space-y-6">
      <div class="max-w-3xl space-y-3">
        <h2 class="text-2xl font-bold tracking-tight">Front-Desk Efficiency Designed for Crowded Morning Queues</h2>
        <p class="text-xs sm:text-sm text-slate-400 leading-relaxed">
          During peak 7:00 AM to 10:00 AM fasting collection hours, every second counts. Aarozi enables full registration, test package selection, payment collection, and barcode printing in under 45 seconds per patient.
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs pt-4 border-t border-slate-800">
        <div><strong class="text-teal-400 block mb-1">Aadhaar & ABHA Ready</strong><span>Optional Aadhaar last 4 digits capture for national health identification compliance.</span></div>
        <div><strong class="text-teal-400 block mb-1">Family Member Linking</strong><span>Manage entire households under a primary contact number with individual sub-UHIDs.</span></div>
        <div><strong class="text-teal-400 block mb-1">Emergency / Stat Toggle</strong><span>Flags urgent ICU or pre-operative samples in high-priority red across all lab benches.</span></div>
        <div><strong class="text-teal-400 block mb-1">Referring Doctor Linking</strong><span>Auto-links commission percentage and referral partner records at registration.</span></div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


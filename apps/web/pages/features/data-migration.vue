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
        Data Export & Software Migration
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Migrate from your existing legacy laboratory software to Aarozi in minutes with our automated Excel & CSV mapping assistant.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="upload" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Excel / CSV Bulk Import</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Upload spreadsheets containing historical patient directories, doctor contacts, test catalogs, and custom price lists. Automated header detection maps columns in seconds.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
          <Icon name="check-circle" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Pre-Flight Validation Preview</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Preview all rows before committing to the database. Highlights invalid phone numbers, duplicate test codes, or missing normal intervals for easy correction.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="download" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Full Data Ownership & Export</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          You are never locked in. Export your entire patient directory, test results, doctor commission records, and GST billing ledgers to Excel/CSV with a single click.
        </p>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


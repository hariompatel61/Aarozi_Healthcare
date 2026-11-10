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
        Business & Clinical Analytics
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Gain real-time visibility into daily revenue collections, top-performing diagnostic tests, referral doctor trends, and turnaround time bottlenecks.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="chart-bar" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Daily Revenue & Collection Trends</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Monitor real-time cash, UPI, card, and credit collections. Compare daily and monthly trends across multiple branches and collection centers.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="clock" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Sample TAT Bottleneck Analysis</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Track time elapsed from patient registration &rarr; sample collection &rarr; analyzer run &rarr; doctor verification. Pinpoints operational delays instantly.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-950 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
          <Icon name="users" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Doctor Referral Performance</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          See which physicians, clinics, and hospitals drive the highest patient volumes and diagnostic revenue with automated commission calculations.
        </p>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


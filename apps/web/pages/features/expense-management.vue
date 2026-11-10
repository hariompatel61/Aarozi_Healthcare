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
        Expense Management & Petty Cash
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Record daily clinical operational expenses, courier fees, machine calibration costs, and staff petty cash with cashier settlement integration.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="currency-rupee" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Daily Cashier Expense Logging</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Log cash payouts directly from the front-desk register (e.g. bio-waste disposal, tea/snacks, emergency cleaning supplies). Subtracts automatically during shift-end settlement.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-950 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
          <Icon name="truck" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Courier & Phlebotomy Fuel</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Track home-collection phlebotomist travel allowances, sample transit ice box courier expenses, and reference lab outsourced testing charges.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="presentation-chart-line" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Net Daily Profit & Loss</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Instantly view True Net Profit by subtracting daily expenses and doctor referral commissions from total gross patient collections.
        </p>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

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
        Cashier Billing & Referral Accounting
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        GST invoicing, multi-mode split payments, doctor commission ledgers, and end-of-shift cash drawer reconciliation.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="shopping-cart" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Split Payment POS Counter</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Accept partial payment in Cash and balance via UPI or Credit Card. Records exact transaction references for foolproof daily bookkeeping.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="users" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Doctor Commission Ledgers</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Configure percentage or test-wise fixed referral incentives for consulting physicians and collection centers. One-click settlement calculation with payment vouchers.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-950 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
          <Icon name="scale" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Shift Settlement & Cash Closing</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Cashiers generate shift-end handover sheets showing total collections, discounts given, refunds issued, and cash in drawer with manager counter-signatures.
        </p>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'
import PricingCalculator from '~/components/marketing/PricingCalculator.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const existingLicenseKey = ref('')
const verified = ref(false)

function checkLicense() {
  if (existingLicenseKey.value.trim().length > 5) {
    verified.value = true
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="refresh" size="xs" />
        <span>Seamless Licence Renewal</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Renew Your Aarozi Healthcare Software Licence
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Extend your active test intake and software updates seamlessly. Zero clinical data loss or disruption to existing laboratory workflows.
      </p>
    </div>

    <!-- Quick License Key Lookup -->
    <div v-if="!verified" class="max-w-xl mx-auto rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 shadow-sm space-y-4 text-center">
      <h3 class="text-base font-bold text-slate-900 dark:text-white">Enter Existing Licence ID or Machine ID</h3>
      <p class="text-xs text-slate-500">Found in your LIS software under Settings > System & Licensing</p>

      <div class="flex gap-2">
        <input
          v-model="existingLicenseKey"
          type="text"
          placeholder="e.g. LIC-PROD-20261109-8F12 or HW-89F4"
          class="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 font-mono text-xs focus:ring-2 focus:ring-teal-500"
        />
        <Button variant="primary" size="sm" @click="checkLicense">
          Lookup
        </Button>
      </div>

      <div class="pt-2 text-xs text-slate-400">
        Or <NuxtLink to="/account" class="text-teal-600 font-bold hover:underline">sign in to your customer account</NuxtLink> to renew with 1 click.
      </div>
    </div>

    <!-- Verified Renewal Options -->
    <div v-else class="space-y-8">
      <div class="p-6 rounded-3xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 flex items-center justify-between max-w-4xl mx-auto">
        <div class="flex items-center space-x-3">
          <div class="w-8 h-8 rounded-full bg-emerald-500 text-white font-bold flex items-center justify-center text-xs">✓</div>
          <div>
            <h4 class="text-sm font-bold text-slate-900 dark:text-white">Active Licence Found: {{ existingLicenseKey }}</h4>
            <p class="text-xs text-emerald-700 dark:text-emerald-300">Renewal discount applied: Early renewal coupon <strong>AAROZI2026</strong> active!</p>
          </div>
        </div>
        <button @click="verified = false" class="text-xs text-slate-500 underline hover:text-slate-800">Change</button>
      </div>

      <PricingCalculator />
    </div>

    <CtaBanner />
  </div>
</template>


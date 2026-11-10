<script setup lang="ts">
import PricingCalculator from '~/components/marketing/PricingCalculator.vue'
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const comparisonRows = [
  { feature: 'Core Pathology LIS (Hematology, Biochem, Serology)', pro: true, enterprise: true },
  { feature: 'Radiology & USG Reporting Templates', pro: true, enterprise: true },
  { feature: 'Integrated Cashier POS & Split Payments', pro: true, enterprise: true },
  { feature: 'Code 128 Sample Barcode Printing', pro: true, enterprise: true },
  { feature: 'Cryptographic Tamper-Evident QR Reports', pro: true, enterprise: true },
  { feature: 'LAN Workstations (Unlimited PCs on Local Hub)', pro: true, enterprise: true },
  { feature: 'Automated 1-Click Backup & Restore', pro: true, enterprise: true },
  { feature: 'Doctor Commission Ledger & Accounting', pro: true, enterprise: true },
  { feature: 'Blood Bank Module & ISBT-128 Tracking', pro: 'Optional Add-on', enterprise: true },
  { feature: 'Software Licence Validity', pro: '1 Year (Annual Renewal)', enterprise: 'Lifetime (Perpetual)' },
  { feature: 'Software Upgrades & Security Patches', pro: 'Included (1 Year)', enterprise: 'Lifetime Included' },
  { feature: 'Priority Phone & Remote AnyDesk Support', pro: 'Standard Support', enterprise: 'Dedicated SLA Support' },
  { feature: 'Hardware Transfer Support', pro: '1 Machine Transfer / yr', enterprise: 'Unlimited Hardware Moves' },
]
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="tag" size="xs" />
        <span>Transparent & Honest Pricing</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Zero Per-Patient Fees. Zero Hidden Surcharges.
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Choose between an affordable annual plan or own the software forever with a perpetual lifetime license. All plans run 100% offline on your Master PC.
      </p>
    </div>

    <!-- Interactive Pricing Calculator -->
    <PricingCalculator />

    <!-- Feature Comparison Matrix -->
    <div class="space-y-6 pt-12">
      <div class="text-center max-w-2xl mx-auto">
        <h2 class="text-2xl font-bold text-slate-900 dark:text-white">Detailed Plan Comparison</h2>
        <p class="text-xs text-slate-500">Every feature transparently detailed with no asterisk surprises.</p>
      </div>

      <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800">
                <th class="py-4 px-6 font-bold text-slate-700 dark:text-slate-300">Feature / Capability</th>
                <th class="py-4 px-6 font-bold text-teal-600 text-center w-48">Yearly Pro (₹14,999)</th>
                <th class="py-4 px-6 font-bold text-indigo-600 text-center w-48">Lifetime Enterprise (₹39,999)</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800/60">
              <tr v-for="row in comparisonRows" :key="row.feature" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                <td class="py-3.5 px-6 font-medium text-slate-900 dark:text-white">{{ row.feature }}</td>
                <td class="py-3.5 px-6 text-center">
                  <span v-if="row.pro === true" class="text-teal-600 font-bold text-sm">✓</span>
                  <span v-else class="text-slate-600 dark:text-slate-400 font-semibold">{{ row.pro }}</span>
                </td>
                <td class="py-3.5 px-6 text-center">
                  <span v-if="row.enterprise === true" class="text-indigo-600 font-bold text-sm">✓</span>
                  <span v-else class="text-slate-600 dark:text-slate-400 font-semibold">{{ row.enterprise }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Frequently Asked Licensing Questions -->
    <div class="p-8 sm:p-12 rounded-3xl bg-slate-900 text-white border border-slate-800 space-y-6">
      <h2 class="text-2xl font-bold tracking-tight">Licensing & Purchase FAQ</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-400">
        <div class="space-y-1.5">
          <h4 class="font-bold text-teal-400 text-sm">What happens if my yearly license expires?</h4>
          <p class="leading-relaxed">Your clinical database and existing reports are never locked or deleted. You retain read-only and export access. Renewing reactivates full test intake instantly.</p>
        </div>
        <div class="space-y-1.5">
          <h4 class="font-bold text-teal-400 text-sm">Can I switch my Master PC if my hard drive crashes?</h4>
          <p class="leading-relaxed">Yes. Our customer portal includes hardware re-keying. Generate a new license file for your replacement PC using your recovery key.</p>
        </div>
        <div class="space-y-1.5">
          <h4 class="font-bold text-teal-400 text-sm">Is GST invoice provided for tax input credit?</h4>
          <p class="leading-relaxed">Yes. Provide your GSTIN during checkout and download an 18% GST tax invoice immediately from your customer account.</p>
        </div>
        <div class="space-y-1.5">
          <h4 class="font-bold text-teal-400 text-sm">Do I need an internet connection to use the software?</h4>
          <p class="leading-relaxed">No. Internet is only used once to download the installer and upload your license key. All day-to-day operations are 100% offline.</p>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


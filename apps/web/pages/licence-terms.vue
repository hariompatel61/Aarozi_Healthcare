<script setup lang="ts">
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
    <!-- Header -->
    <div class="text-center space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="key" size="xs" />
        <span>Software Licensing Agreement</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Aarozi End-User Licence Terms
      </h1>
      <p class="text-xs sm:text-sm text-slate-500">Edition: 2026-v1.0.4-LTS</p>
    </div>

    <!-- Core Tenet Alert -->
    <div class="p-8 rounded-3xl bg-slate-900 text-white border border-slate-800 space-y-3">
      <h3 class="text-base font-bold text-teal-400">The Non-Negotiable Data Safety Clause</h3>
      <p class="text-xs sm:text-sm text-slate-300 leading-relaxed">
        Under no circumstances shall the expiration or non-renewal of an Aarozi software license result in the deletion, corruption, or hostage-taking of clinical, patient, or financial records. Laboratories retain permanent read-only and export access to their local relational database.
      </p>
    </div>

    <!-- Clauses -->
    <div class="space-y-8 text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">1. Licence Types</h2>
        <div class="space-y-3">
          <div class="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <h4 class="font-bold text-slate-900 dark:text-white mb-1">A. Free Evaluation Trial (14 Days)</h4>
            <p class="text-xs text-slate-500">Allows unrestricted evaluation of all pathology, radiology, barcoding, and billing modules on a single Master PC with up to 50 test entries.</p>
          </div>
          <div class="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <h4 class="font-bold text-teal-600 mb-1">B. Yearly Pro Licence (Annual)</h4>
            <p class="text-xs text-slate-500">Grants active test registration, report issuance, and feature updates for 365 calendar days from activation date. Includes standard technical support.</p>
          </div>
          <div class="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <h4 class="font-bold text-indigo-600 mb-1">C. Lifetime Enterprise Licence (Perpetual)</h4>
            <p class="text-xs text-slate-500">Grants a permanent, non-expiring right to use the software on the licensed Master PC. Includes lifetime software updates and priority SLA support.</p>
          </div>
        </div>
      </section>

      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">2. Hardware Binding & Cryptographic Verification</h2>
        <p>Aarozi licenses are cryptographically signed using Ed25519 digital signatures and bound to the laboratory’s Master PC unique hardware identifier (CPU ID, motherboard UUID, and drive serial). A license file (.lic) is valid exclusively for the machine for which it was generated.</p>
      </section>

      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">3. Hardware Migration Policy</h2>
        <p>If the licensee upgrades or replaces their Master PC due to hardware obsolescence or failure, they may submit their new Machine ID through the Aarozi Customer Account portal to receive a replacement license file. Yearly Pro licenses include one free hardware re-keying per year; Lifetime Enterprise licenses include unlimited transfers.</p>
      </section>

      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">4. Offline Verification & Anti-Clock Rollback</h2>
        <p>Licence validity is verified entirely locally on the Master PC without requiring an active internet connection. To prevent manipulation, the software incorporates monotonic audit checkpoints; rolling back the system clock does not extend validity.</p>
      </section>
    </div>

    <CtaBanner />
  </div>
</template>


<script setup lang="ts">
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
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="heart" size="xs" />
        <span>Our Mission & Principles</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Engineering Medical Software for Uncompromised Diagnostic Freedom
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        We believe healthcare diagnostic centers should own their tools, control their patient data, and never face downtime due to remote cloud outages.
      </p>
    </div>

    <!-- Core Philosophy Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="shield" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Absolute Data Sovereignty</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Diagnostic findings belong exclusively to the patient and doctor. We never upload, scrape, sell, or hold your medical databases hostage behind recurring paywalls.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
          <Icon name="zap" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Zero Cloud Dependency</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Broadband fails. Fibre cables get cut. Aarozi's local-first LAN Hub ensures your receptionists, phlebotomists, and pathologists work without missing a single beat.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="award" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Radical Engineering Integrity</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          We reject microservices bloat and unnecessary dependencies. Aarozi is built as a lightning-fast native binary that runs flawlessly on standard Windows hardware.
        </p>
      </div>
    </div>

    <!-- Company Background & Engineering Standards -->
    <div class="p-8 sm:p-12 rounded-3xl bg-slate-900 text-white border border-slate-800 space-y-6">
      <div class="max-w-3xl space-y-3">
        <h2 class="text-2xl font-bold tracking-tight">Built by Medical Software Engineers in India</h2>
        <p class="text-xs sm:text-sm text-slate-400 leading-relaxed">
          Headquartered in India, Aarozi Healthcare was founded to solve the acute pain points of diagnostic centers: crippling monthly SaaS bills, sluggish web apps during peak morning rushes, and data loss during internet drops. We engineered Aarozi to be the most resilient laboratory information system on the market.
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs pt-4 border-t border-slate-800">
        <div><strong class="text-teal-400 block mb-1">NABL & ISO Aligned</strong><span>Compliant with standard reference intervals and digital signature verifications.</span></div>
        <div><strong class="text-teal-400 block mb-1">Ed25519 Cryptography</strong><span>Tamper-evident verification without requiring central cloud lookups.</span></div>
        <div><strong class="text-teal-400 block mb-1">Affordable Pricing</strong><span>Fair licensing with honest perpetual lifetime ownership options.</span></div>
        <div><strong class="text-teal-400 block mb-1">Dedicated Support</strong><span>Direct WhatsApp and remote desktop assistance from real software engineers.</span></div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

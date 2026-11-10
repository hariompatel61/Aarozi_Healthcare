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
        <Icon name="file-text" size="xs" />
        <span>Legal Terms</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Terms of Service
      </h1>
      <p class="text-xs sm:text-sm text-slate-500">Effective Date: 10 November 2026</p>
    </div>

    <!-- Terms Body -->
    <div class="space-y-8 text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">1. Acceptance of Terms</h2>
        <p>By registering on https://www.labs.aarozi.in/, purchasing a software license, or downloading the Aarozi LIS desktop installer, you agree to comply with and be bound by these Terms of Service. If you do not agree to these terms, please do not use the service or software.</p>
      </section>

      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">2. Scope of Software</h2>
        <p>Aarozi Healthcare provides an on-premise, offline-first Laboratory Information System (LIS) and Radiology Information System (RIS) designed to manage diagnostic workflow, sample tracking, report generation, and billing on the customer’s local computer hardware.</p>
      </section>

      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">3. Customer Responsibilities</h2>
        <p>The customer (laboratory owner) is solely responsible for maintaining the physical security of their Master PC, ensuring regular scheduled database backups to external media, and verifying the medical accuracy and clinical validity of all pathology and radiology reports released by their licensed staff.</p>
      </section>

      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">4. Intellectual Property</h2>
        <p>All software binaries, user interfaces, branding, and proprietary algorithms of Aarozi Healthcare are the intellectual property of Aarozi Healthcare. The customer is granted a non-exclusive license to use the software in accordance with their purchased plan.</p>
      </section>

      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">5. Governing Law and Jurisdiction</h2>
        <p>These terms shall be governed by and construed in accordance with the laws of the Republic of India. Any disputes arising out of these terms shall be subject to the exclusive jurisdiction of the competent courts in India.</p>
      </section>
    </div>

    <CtaBanner />
  </div>
</template>


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
        Tamper-Evident QR-Coded Diagnostic Reports
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Empower referring doctors and patients to instantly verify report authenticity with standard smartphone cameras while keeping internal clinical databases strictly private.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="qrcode" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Instant Smartphone Verification</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Every generated PDF contains a cryptographic SHA-256 verification QR code. Any camera scan opens an authenticated digital proof showing patient name, test date, and authorized signing doctor.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-rose-100 dark:bg-rose-950 text-rose-600 dark:text-rose-400 flex items-center justify-center font-bold">
          <Icon name="shield" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Fraud & Tamper Prevention</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Protects your diagnostic center's reputation against forged medical certificates or altered hemoglobin/sugar values submitted for insurance, visa, or employment clearances.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
          <Icon name="lock" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Isolated Public Verification Gateway</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          The public QR gateway only verifies the specific report payload without opening any network ports to your local LAN or master PC database, preserving complete clinical confidentiality.
        </p>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


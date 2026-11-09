<script setup lang="ts">
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import ToastProvider from '~/components/ui/ToastProvider.vue'
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100 flex flex-col selection:bg-teal-600 selection:text-white">
    <!-- Marketing Navigation Header -->
    <header class="sticky top-0 z-50 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <!-- Brand Logo -->
        <NuxtLink to="/" class="flex items-center space-x-2.5 group">
          <div class="w-9 h-9 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold text-base shadow-sm group-hover:bg-teal-700 transition-colors">
            AH
          </div>
          <div>
            <span class="font-bold text-base tracking-tight text-slate-900 dark:text-white">Aarozi Healthcare</span>
            <span class="hidden sm:inline-block ml-1.5 px-2 py-0.5 text-[10px] font-semibold bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300 rounded-full border border-teal-200 dark:border-teal-800">LIS & Blood Bank</span>
          </div>
        </NuxtLink>

        <!-- Navigation Links -->
        <nav class="hidden md:flex items-center space-x-8 text-sm font-medium text-slate-600 dark:text-slate-300">
          <a href="#features" class="hover:text-teal-600 dark:hover:text-teal-400 transition-colors">Features</a>
          <a href="#pathology" class="hover:text-teal-600 dark:hover:text-teal-400 transition-colors">Pathology LIS</a>
          <a href="#bloodbank" class="hover:text-teal-600 dark:hover:text-teal-400 transition-colors">Blood Bank</a>
          <a href="#pricing" class="hover:text-teal-600 dark:hover:text-teal-400 transition-colors">Pricing & Plans</a>
          <NuxtLink to="/design-system" class="hover:text-teal-600 dark:hover:text-teal-400 transition-colors">Design System</NuxtLink>
        </nav>

        <!-- Right Action CTAs -->
        <div class="flex items-center space-x-3">
          <NuxtLink to="/login">
            <Button variant="secondary" size="sm">
              <template #icon-left><Icon name="lock" size="xs" /></template>
              Staff Login
            </Button>
          </NuxtLink>
          <a href="#pricing">
            <Button variant="primary" size="sm">
              Get Started
            </Button>
          </a>
        </div>
      </div>
    </header>

    <!-- Page Body Slot -->
    <main class="flex-1 w-full">
      <slot />
    </main>

    <!-- Clean Commercial Marketing Footer -->
    <footer class="bg-slate-900 text-slate-400 border-t border-slate-800 text-xs">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 grid grid-cols-1 md:grid-cols-4 gap-8 text-left">
        <div class="space-y-3">
          <div class="flex items-center space-x-2">
            <div class="w-7 h-7 rounded-lg bg-teal-600 text-white flex items-center justify-center font-bold text-xs">AH</div>
            <span class="font-bold text-sm text-white">Aarozi Healthcare</span>
          </div>
          <p class="text-slate-400 text-xs leading-relaxed">
            Zero-Central-Patient-Hosting, offline-first Laboratory Information System (LIS) & Blood Bank management software for modern diagnostic laboratories in India.
          </p>
          <div class="text-[11px] text-teal-400 font-mono">
            Ed25519 Cryptographically Licensed Software
          </div>
        </div>

        <div>
          <h4 class="font-bold text-white mb-3 text-xs uppercase tracking-wider">Clinical Modules</h4>
          <ul class="space-y-2 text-xs">
            <li><a href="#features" class="hover:text-white transition">Patient Registration & UHID</a></li>
            <li><a href="#features" class="hover:text-white transition">Automated Analyzer Interfacing</a></li>
            <li><a href="#features" class="hover:text-white transition">Barcode Tracking & Samples</a></li>
            <li><a href="#features" class="hover:text-white transition">Pathologist Verification & Signing</a></li>
            <li><a href="#features" class="hover:text-white transition">WhatsApp QR Report Delivery</a></li>
          </ul>
        </div>

        <div>
          <h4 class="font-bold text-white mb-3 text-xs uppercase tracking-wider">Commercial Plans</h4>
          <ul class="space-y-2 text-xs">
            <li><a href="#pricing" class="hover:text-white transition">Plan A: Annual Subscription (₹14,999)</a></li>
            <li><a href="#pricing" class="hover:text-white transition">Plan B: Lifetime License (₹39,999)</a></li>
            <li><a href="#pricing" class="hover:text-white transition">Customer-Owned Google Drive Backup</a></li>
            <li><a href="#pricing" class="hover:text-white transition">Offline Hardware Machine Lock</a></li>
          </ul>
        </div>

        <div>
          <h4 class="font-bold text-white mb-3 text-xs uppercase tracking-wider">Compliance & Standards</h4>
          <p class="text-xs text-slate-400 leading-relaxed mb-3">
            Designed to meet NABL (ISO 15189:2022) documentation standards, DISHA patient privacy principles, and GST e-invoicing compliance.
          </p>
          <div class="text-[11px] text-slate-500">
            &copy; 2026 Aarozi Healthcare. All rights reserved.
          </div>
        </div>
      </div>
    </footer>

    <!-- Global Toast Notifications -->
    <ToastProvider />
  </div>
</template>

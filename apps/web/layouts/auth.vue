<script setup lang="ts">
import ToastProvider from '~/components/ui/ToastProvider.vue'
</script>

<template>
  <div class="min-h-screen bg-[#090d16] flex flex-col justify-between items-center p-4 selection:bg-teal-600 selection:text-white font-sans text-slate-200 relative overflow-hidden">
    <!-- Subtle Background Radial Accents -->
    <div class="absolute -top-40 -left-40 w-96 h-96 bg-teal-600/10 rounded-full blur-3xl pointer-events-none" />
    <div class="absolute -bottom-40 -right-40 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

    <!-- Top LAN Status Bar -->
    <header class="w-full max-w-5xl py-4 flex items-center justify-between z-10">
      <NuxtLink to="/" class="flex items-center space-x-2 text-slate-300 hover:text-white transition-colors">
        <div class="w-7 h-7 rounded-lg bg-teal-600 text-white flex items-center justify-center font-bold text-xs shadow-xs">
          AH
        </div>
        <span class="font-bold text-sm tracking-tight text-white">Aarozi Healthcare</span>
      </NuxtLink>

      <!-- Local LAN Health Badge -->
      <div class="inline-flex items-center space-x-2 bg-slate-900/90 px-3 py-1 rounded-full border border-slate-800 text-xs shadow-xs">
        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <span class="font-medium text-slate-300">Local LAN Server Active</span>
        <span class="text-slate-600">&bull;</span>
        <span class="font-mono text-[11px] text-teal-400">192.168.1.100</span>
      </div>
    </header>

    <!-- Main Centered Authentication Form -->
    <main class="w-full max-w-md my-auto py-6 z-10">
      <slot />
    </main>

    <!-- Minimal Offline Footer -->
    <footer class="w-full max-w-5xl py-4 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 z-10 border-t border-slate-800/60 gap-2">
      <div class="flex items-center space-x-2">
        <span>Offline-First LIS</span>
        <span>&bull;</span>
        <span class="font-mono text-[11px]">Machine ID: ED25-8841-B72F</span>
      </div>
      <div>
        <span>NABL & ISO 15189:2022 Compliant Architecture</span>
      </div>
    </footer>

    <!-- Global Toast Provider -->
    <ToastProvider />
  </div>
</template>


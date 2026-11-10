<script setup lang="ts">
import ToastProvider from '~/components/ui/ToastProvider.vue'
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-between items-center p-4 selection:bg-teal-600 selection:text-white font-sans text-slate-900 dark:text-slate-100 relative">
    <!-- Top Minimal Navigation -->
    <header class="w-full max-w-5xl py-4 flex items-center justify-between z-10">
      <NuxtLink to="/" class="flex items-center space-x-2.5 group">
        <div class="w-8 h-8 rounded-xl bg-teal-600 text-white flex items-center justify-center font-black text-sm shadow-sm group-hover:bg-teal-700 transition-colors">
          AH
        </div>
        <span class="font-bold text-base tracking-tight text-slate-900 dark:text-white">Aarozi Healthcare</span>
      </NuxtLink>

      <NuxtLink to="/" class="text-xs font-semibold text-slate-500 hover:text-teal-600 dark:text-slate-400 dark:hover:text-teal-400 transition-colors flex items-center space-x-1">
        <span>← Back to website</span>
      </NuxtLink>
    </header>

    <!-- Main Centered Authentication Form -->
    <main class="w-full max-w-md my-auto py-8 z-10">
      <slot />
    </main>

    <!-- Simple Professional Footer -->
    <footer class="w-full max-w-5xl py-4 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 dark:text-slate-500 z-10 border-t border-slate-200 dark:border-slate-800 gap-2">
      <div>
        <span>&copy; 2026 Aarozi Healthcare. All rights reserved.</span>
      </div>
      <div class="flex items-center space-x-4">
        <NuxtLink to="/privacy" class="hover:underline">Privacy Policy</NuxtLink>
        <span>&bull;</span>
        <NuxtLink to="/terms" class="hover:underline">Terms of Service</NuxtLink>
        <span>&bull;</span>
        <NuxtLink to="/support" class="hover:underline">Support</NuxtLink>
      </div>
    </footer>

    <!-- Global Toast Provider -->
    <ToastProvider />
  </div>
</template>

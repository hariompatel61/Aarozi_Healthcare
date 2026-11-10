<script setup lang="ts">
import { useTheme } from '~/composables/useTheme'
import Icon from '~/components/ui/Icon.vue'
import ToastProvider from '~/components/ui/ToastProvider.vue'

const { isDark, toggleTheme } = useTheme()
</script>

<template>
  <div
    class="min-h-screen w-full bg-[#f9f8fe] dark:bg-[#0e101c] text-slate-900 dark:text-slate-100 flex flex-col justify-between items-center p-4 sm:p-6 transition-colors duration-200 relative selection:bg-[#bee1fb] selection:text-[#1c4372]"
    style="display: flex; flex-direction: column; min-height: 100vh; justify-content: space-between; align-items: center;"
  >
    <!-- Top Minimal Navigation Bar -->
    <header class="w-full max-w-5xl py-4 flex items-center justify-between z-10 shrink-0">
      <NuxtLink to="/" class="flex items-center space-x-2.5 group">
        <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-[#2576d2] to-[#5eaef5] text-white flex items-center justify-center font-black text-sm shadow-sm group-hover:from-[#1c5fae] group-hover:to-[#3b93ee] transition-all">
          AH
        </div>
        <span class="font-bold text-base tracking-tight text-slate-900 dark:text-white transition-colors">
          Aarozi Healthcare
        </span>
      </NuxtLink>

      <div class="flex items-center space-x-3 sm:space-x-4">
        <!-- Minimal Light / Dark Mode Toggle -->
        <button
          type="button"
          class="p-2 rounded-lg text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
          aria-label="Toggle theme"
          @click="toggleTheme"
        >
          <Icon :name="isDark ? 'sun' : 'moon'" size="sm" />
        </button>

        <NuxtLink
          to="/"
          class="text-xs font-semibold text-slate-600 hover:text-[#2576d2] dark:text-slate-400 dark:hover:text-[#90ccf9] transition-colors flex items-center space-x-1"
        >
          <span>&larr; Back to website</span>
        </NuxtLink>
      </div>
    </header>

    <!-- Main Centered Authentication Form Card -->
    <main class="w-full max-w-md my-auto py-8 z-10 flex flex-col items-center">
      <div class="w-full">
        <slot />
      </div>
    </main>

    <!-- Simple Professional Footer -->
    <footer class="w-full max-w-5xl py-4 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-600 dark:text-slate-400 z-10 border-t border-[#ede9f7] dark:border-[#23273e] gap-2 shrink-0">
      <div>
        <span>&copy; 2026 Aarozi Healthcare. All rights reserved.</span>
      </div>
      <div class="flex items-center space-x-4">
        <NuxtLink to="/privacy" class="hover:text-[#2576d2] dark:hover:text-[#90ccf9] transition-colors">Privacy Policy</NuxtLink>
        <span>&bull;</span>
        <NuxtLink to="/terms" class="hover:text-[#2576d2] dark:hover:text-[#90ccf9] transition-colors">Terms of Service</NuxtLink>
        <span>&bull;</span>
        <NuxtLink to="/support" class="hover:text-[#2576d2] dark:hover:text-[#90ccf9] transition-colors">Support</NuxtLink>
      </div>
    </footer>

    <!-- Global Toast Provider -->
    <ToastProvider />
  </div>
</template>

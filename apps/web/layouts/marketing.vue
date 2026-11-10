<script setup lang="ts">
import MarketingNav from '~/components/marketing/MarketingNav.vue'
import MarketingFooter from '~/components/marketing/MarketingFooter.vue'
import ToastProvider from '~/components/ui/ToastProvider.vue'
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100 flex flex-col selection:bg-teal-600 selection:text-white">
    <!-- Marketing Navigation Header with Mega-Dropdowns -->
    <MarketingNav />

    <!-- Page Body Slot -->
    <main class="flex-1 w-full">
      <slot />
    </main>

    <!-- Comprehensive Marketing Footer -->
    <MarketingFooter />

    <!-- Toast Notifications Provider -->
    <ToastProvider />
  </div>
</template>

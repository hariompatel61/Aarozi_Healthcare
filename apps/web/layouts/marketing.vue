<script setup lang="ts">
import MarketingNav from '~/components/marketing/MarketingNav.vue'
import MarketingFooter from '~/components/marketing/MarketingFooter.vue'
import ToastProvider from '~/components/ui/ToastProvider.vue'
</script>

<template>
  <div class="min-h-screen bg-[#f9f8fe] dark:bg-[#0e101c] font-sans text-slate-900 dark:text-slate-100 flex flex-col selection:bg-[#bee1fb] selection:text-[#1c4372]">
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

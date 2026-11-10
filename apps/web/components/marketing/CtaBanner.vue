<script setup lang="ts">
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'

defineProps<{
  title?: string
  subtitle?: string
}>()
</script>

<template>
  <section class="bg-gradient-to-br from-slate-900 via-slate-900 to-teal-950 text-white rounded-3xl p-8 sm:p-12 lg:p-16 my-16 border border-slate-800 shadow-2xl relative overflow-hidden text-center sm:text-left">
    <!-- Background Glow -->
    <div class="absolute -right-20 -bottom-20 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

    <div class="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-8 relative z-10">
      <div class="space-y-3 max-w-xl">
        <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs font-bold uppercase tracking-wider">
          <Icon name="shield" size="xs" />
          <span>Offline-First Guarantee</span>
        </div>
        <h2 class="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white leading-tight">
          {{ title || 'Ready to Run Your Laboratory with Complete Reliability?' }}
        </h2>
        <p class="text-sm sm:text-base text-slate-300">
          {{ subtitle || 'Install Aarozi on your master PC today. Start registering patients, generating barcode tube labels, and releasing authorized reports in under 15 minutes.' }}
        </p>
      </div>

      <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0 w-full sm:w-auto">
        <NuxtLink to="/pricing">
          <Button variant="primary" size="lg" class="w-full justify-center">
            View Transparent Pricing
          </Button>
        </NuxtLink>
        <NuxtLink to="/download">
          <Button variant="secondary" size="lg" class="w-full justify-center">
            <template #icon-left><Icon name="arrow-down" size="sm" /></template>
            Download v1.0.4 Installer
          </Button>
        </NuxtLink>
      </div>
    </div>
  </section>
</template>


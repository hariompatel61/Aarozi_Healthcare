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
        Barcode & Specimen Management
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Eliminate pre-analytical specimen mix-ups with automated thermal tube labeling, color guides, and chain-of-custody tracking.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="qr-code" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">One-Click Thermal Printing</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Generates crisp Code 128 and 2D Datamatrix labels compatible with all standard thermal printers (Zebra, TSC, Citizen, Honeywell) in 50x25mm and 38x25mm tube sizes.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-950 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
          <Icon name="color-swatch" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Color-Coded Tube Guidance</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Phlebotomists see visual color-coded prompts for every required vacutainer: Purple for EDTA Hematology, Gold/Yellow for Serum Gel, Grey for Sodium Fluoride Glucose.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-rose-100 dark:bg-rose-950 text-rose-600 dark:text-rose-400 flex items-center justify-center font-bold">
          <Icon name="x-circle" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Specimen Rejection Audit</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Log hemolyzed, clotted, insufficient volume, or lipemic samples with formal rejection notices. Triggers automated SMS/WhatsApp alerts for recollection.
        </p>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


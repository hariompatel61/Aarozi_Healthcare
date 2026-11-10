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
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="file-text" size="xs" />
        <span>Imaging Solution</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Structured Reporting for Ultrasound, X-Ray & Imaging Centres
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Empower Radiologists and Sonologists with rich structured reporting templates, macro shortcuts, organ-specific organ assessment, and rapid PDF generation.
      </p>
    </div>

    <!-- Core Capabilities Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="edit" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Structured Organ-by-Organ Templates</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Pre-built normal templates for USG Whole Abdomen, Pelvis, KUB, Obstetric (Trimester 1, 2, 3), Scrotum, Thyroid, and Musculoskeletal studies.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
          <Icon name="zap" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Typing Macros & Clinical Auto-Text</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Insert standard clinical findings (e.g. "Fatty Liver Grade 1", "Renal Calculus 4mm lower pole") with one-click macro keywords. Finish reports in under 90 seconds.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="check-circle" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">PNDT & Form F Record Keeping</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Built-in mandatory statutory compliance fields for Indian radiodiagnostic regulations, ensuring proper documentation for all obstetric imaging studies.
        </p>
      </div>
    </div>

    <!-- Supported Modalities -->
    <div class="p-8 sm:p-12 rounded-3xl bg-slate-900 text-white border border-slate-800 space-y-6">
      <h2 class="text-2xl font-bold tracking-tight">Multi-Modality Template Support</h2>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
        <div class="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/60">
          <span class="text-teal-400 font-bold block text-sm">Ultrasound (USG)</span>
          <span class="text-[11px] text-slate-400">Abdomen, Pelvis, TVS, Doppler</span>
        </div>
        <div class="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/60">
          <span class="text-teal-400 font-bold block text-sm">Digital X-Ray</span>
          <span class="text-[11px] text-slate-400">Chest PA, Spine, Joints, Bones</span>
        </div>
        <div class="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/60">
          <span class="text-teal-400 font-bold block text-sm">Electrocardiogram</span>
          <span class="text-[11px] text-slate-400">12-Lead ECG rhythm analysis</span>
        </div>
        <div class="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/60">
          <span class="text-teal-400 font-bold block text-sm">Echocardiography</span>
          <span class="text-[11px] text-slate-400">2D Echo, Doppler EF% assessment</span>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

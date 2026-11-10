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
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800">
        <Icon name="heart" size="xs" />
        <span>Clinical Solution</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Blood Bank & Transfusion Medicine Management
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        End-to-end donor screening, mandatory TTI serological testing, component separation, cold-chain temperature logs, cross-matching, and blood bag issue dispatch.
      </p>
    </div>

    <!-- Core Capabilities Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-rose-100 dark:bg-rose-950 text-rose-600 dark:text-rose-400 flex items-center justify-center font-bold">
          <Icon name="user" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Donor Screening & Deferral Registry</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Pre-donation vital check (Hb, BP, Weight, Medical History). Automatic permanent and temporary deferral tracking to protect donor safety and recipient well-being.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400 flex items-center justify-center font-bold">
          <Icon name="shield" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Mandatory TTI Testing</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Screening protocols for Transfusion Transmissible Infections: HIV 1 & 2, Hepatitis B (HBsAg), Hepatitis C (HCV), Syphilis (VDRL), and Malaria before bag release.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="layers" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Component Separation & Stock</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Real-time stock by blood group (A+, B+, O+, AB+, etc.) and components: Packed Red Blood Cells (PRBC), Fresh Frozen Plasma (FFP), Platelet Concentrate (RDP/SDP), and Cryoprecipitate.
        </p>
      </div>
    </div>

    <!-- Blood Bank Workflow Detail -->
    <div class="p-8 sm:p-12 rounded-3xl bg-slate-900 text-white border border-slate-800 space-y-6">
      <div class="max-w-3xl space-y-3">
        <h2 class="text-2xl font-bold tracking-tight">Zero-Error Cross-Match & Emergency Dispatch</h2>
        <p class="text-xs sm:text-sm text-slate-400 leading-relaxed">
          Major and minor compatibility cross-matching ensures safe transfusion. Includes urgent O-negative emergency release protocols with dual-technician signoff.
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs pt-4 border-t border-slate-800">
        <div><strong class="text-rose-400 block mb-1">Cold Storage Logging</strong><span>Monitor deep-freezer and blood bank refrigerator temperature compliance.</span></div>
        <div><strong class="text-rose-400 block mb-1">ISBT 128 Bag Barcodes</strong><span>Track parent donation to derived child components with unique barcodes.</span></div>
        <div><strong class="text-rose-400 block mb-1">Expiry Date Sentinel</strong><span>Color-coded countdown alert before platelet (5-day) or PRBC (35/42-day) expiry.</span></div>
        <div><strong class="text-rose-400 block mb-1">Transfusion Reaction Audit</strong><span>Record post-transfusion adverse reaction investigation records.</span></div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


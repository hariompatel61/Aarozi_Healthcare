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
      <NuxtLink to="/features" class="inline-flex items-center space-x-1.5 text-xs font-bold text-teal-600 hover:underline">
        <Icon name="arrow-left" size="xs" />
        <span>All Features</span>
      </NuxtLink>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Local-First LAN Hub Architecture
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Run your entire diagnostic centre seamlessly on your local network without internet dependence. 1 Master PC + up to 50 concurrent LAN workstations.
      </p>
    </div>

    <!-- Core Capabilities Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="zap" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Zero Cloud Downtime</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Internet outages, ISP fiber cuts, or cloud maintenance never freeze your front desk. Patient registration, billing, and report dispatch proceed without interruption.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
          <Icon name="device-desktop" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Multi-Station Concurrent Access</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Phlebotomy, biochemistry analyzer benches, ultrasound reporting rooms, and cashier counters connect concurrently over Ethernet or Wi-Fi to the Master PC.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="lock" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Zero Third-Party Data Exposure</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Diagnostic findings, abnormal values, and patient billing records remain strictly within the physical boundaries of your medical facility.
        </p>
      </div>
    </div>

    <!-- Network Topology Detail Card -->
    <div class="p-8 sm:p-12 rounded-3xl bg-slate-900 text-white border border-slate-800 space-y-6">
      <div class="max-w-3xl space-y-3">
        <h2 class="text-2xl font-bold tracking-tight">How the Aarozi Local-First LAN Topology Operates</h2>
        <p class="text-xs sm:text-sm text-slate-400 leading-relaxed">
          Aarozi runs as a dedicated high-performance local server on your lab's primary Windows PC. Client workstations open standard web browsers (Chrome, Edge) to access the system instantly without installing any client-side software.
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs pt-4 border-t border-slate-800">
        <div><strong class="text-teal-400 block mb-1">Master Server PC</strong><span>Hosts high-speed embedded database, print engine, and API core.</span></div>
        <div><strong class="text-teal-400 block mb-1">Client Workstations</strong><span>Connect via URL (e.g., http://192.168.1.100:8000) on any PC, laptop, or tablet.</span></div>
        <div><strong class="text-teal-400 block mb-1">Low Latency (&lt;10ms)</strong><span>Instant screen transitions without internet loading spinners or buffering.</span></div>
        <div><strong class="text-teal-400 block mb-1">Automatic Station Binding</strong><span>Bind thermal label printers or receipt printers directly to specific desks.</span></div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


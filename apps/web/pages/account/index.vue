<script setup lang="ts">
import { onMounted } from 'vue'
import { useCustomerAuth } from '~/composables/useCustomerAuth'
import { usePlatformStore } from '~/composables/usePlatformStore'
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'
import Badge from '~/components/ui/Badge.vue'

definePageMeta({
  layout: 'customer',
})

const { profile, licenses, downloadLicenseFile } = useCustomerAuth()
const { windowsRelease, initStore } = usePlatformStore()

onMounted(() => {
  initStore()
})
</script>

<template>
  <div class="space-y-8 text-slate-900 dark:text-slate-100">
    <!-- Welcome Banner (Powder Blue Gradient) -->
    <div class="p-8 rounded-3xl bg-gradient-to-r from-[#1c4372] via-[#2576d2] to-[#1c508e] text-white shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
      <div class="space-y-2">
        <span class="text-xs font-bold uppercase tracking-wider text-[#bee1fb]">Customer Account Console</span>
        <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight">Welcome, {{ profile.lab_name }}</h1>
        <p class="text-xs text-blue-100 max-w-2xl leading-relaxed">
          Manage your offline Master PC software licences, download the official Windows installer (.exe), and activate your local laboratory hub.
        </p>
      </div>

      <div class="flex items-center space-x-3 shrink-0">
        <a :href="windowsRelease.downloadUrl" download>
          <Button variant="secondary" size="md" class="font-bold shadow-md">
            <template #icon-left><Icon name="download" size="xs" /></template>
            <span>Download {{ windowsRelease.version }} (.exe)</span>
          </Button>
        </a>
      </div>
    </div>

    <!-- Metrics Cards (Soft Lavender Cards with High-Contrast Numbers) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="p-5 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] shadow-2xs space-y-1">
        <span class="text-xs font-semibold text-slate-500">Active Licences</span>
        <div class="text-2xl font-black text-slate-900 dark:text-white">{{ licenses.filter(l => l.status === 'ACTIVE').length }}</div>
        <span class="text-[11px] text-[#2576d2] font-bold">Hardware bound &amp; verified</span>
      </div>

      <div class="p-5 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] shadow-2xs space-y-1">
        <span class="text-xs font-semibold text-slate-500">Primary Plan</span>
        <div class="text-2xl font-black text-slate-900 dark:text-white">Yearly Pro</div>
        <span class="text-[11px] text-slate-400">Valid until Nov 2027</span>
      </div>

      <div class="p-5 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] shadow-2xs space-y-1">
        <span class="text-xs font-semibold text-slate-500">LAN Workstations</span>
        <div class="text-2xl font-black text-slate-900 dark:text-white">Unlimited</div>
        <span class="text-[11px] text-emerald-600 font-bold">Local Hub Active</span>
      </div>

      <div class="p-5 rounded-2xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] shadow-2xs space-y-1">
        <span class="text-xs font-semibold text-slate-500">Support Level</span>
        <div class="text-2xl font-black text-slate-900 dark:text-white">Priority SLA</div>
        <span class="text-[11px] text-[#2576d2] font-bold">Phone &amp; AnyDesk</span>
      </div>
    </div>

    <!-- Offline LIS Setup Guide Banner -->
    <div class="p-6 rounded-3xl bg-[#f0f7fe] dark:bg-[#1d273d] border border-[#bee1fb] dark:border-[#2576d2]/50 shadow-2xs space-y-3">
      <div class="flex items-center space-x-2">
        <Icon name="check-circle" size="sm" class="text-[#2576d2]" />
        <h3 class="text-sm font-bold text-slate-900 dark:text-white">Quick Offline Setup Instructions for Your Lab</h3>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-600 dark:text-slate-300">
        <div class="p-3 bg-white dark:bg-[#15182a] rounded-xl border border-[#ede9f7] dark:border-[#23273e] space-y-1">
          <div class="font-bold text-[#2576d2]">1. Download Windows App</div>
          <p>Download the installer (.exe) onto your laboratory master PC.</p>
        </div>
        <div class="p-3 bg-white dark:bg-[#15182a] rounded-xl border border-[#ede9f7] dark:border-[#23273e] space-y-1">
          <div class="font-bold text-[#2576d2]">2. Download License File</div>
          <p>Click "Download .license" below to save your cryptographically signed key.</p>
        </div>
        <div class="p-3 bg-white dark:bg-[#15182a] rounded-xl border border-[#ede9f7] dark:border-[#23273e] space-y-1">
          <div class="font-bold text-[#2576d2]">3. Run 100% Offline</div>
          <p>Launch the app on your Master PC. Connect counter PCs over LAN with zero internet needed.</p>
        </div>
      </div>
    </div>

    <!-- Active Licences Quick Table -->
    <div class="rounded-3xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] overflow-hidden shadow-2xs">
      <div class="p-6 border-b border-[#ede9f7] dark:border-[#23273e] flex items-center justify-between">
        <div>
          <h3 class="text-base font-bold text-slate-900 dark:text-white">Active Software Licences</h3>
          <p class="text-xs text-slate-500">Deploy these cryptographic keys on your Master PC</p>
        </div>
        <NuxtLink to="/account/licences" class="text-xs font-bold text-[#2576d2] hover:underline">
          View All &amp; Re-Key →
        </NuxtLink>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead>
            <tr class="bg-[#f0f7fe]/60 dark:bg-[#1d273d]/60 border-b border-[#ede9f7] dark:border-[#23273e] text-slate-600 dark:text-slate-400 font-bold">
              <th class="py-3 px-6">Licence Key ID</th>
              <th class="py-3 px-6">Plan</th>
              <th class="py-3 px-6">Bound Machine ID</th>
              <th class="py-3 px-6">Valid Until</th>
              <th class="py-3 px-6">Status</th>
              <th class="py-3 px-6 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[#ede9f7] dark:divide-[#23273e]">
            <tr v-for="lic in licenses" :key="lic.license_id" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
              <td class="py-3.5 px-6 font-mono font-bold text-slate-900 dark:text-white">{{ lic.license_id }}</td>
              <td class="py-3.5 px-6 font-medium">{{ lic.plan_code }}</td>
              <td class="py-3.5 px-6 font-mono text-slate-500">{{ lic.installation_id || 'Pending Activation' }}</td>
              <td class="py-3.5 px-6 text-slate-600 dark:text-slate-400">09 Nov 2027</td>
              <td class="py-3.5 px-6">
                <Badge variant="success" size="sm">
                  {{ lic.status }}
                </Badge>
              </td>
              <td class="py-3.5 px-6 text-right">
                <button
                  type="button"
                  class="text-xs font-bold text-[#2576d2] dark:text-[#90ccf9] hover:underline flex items-center space-x-1 ml-auto cursor-pointer"
                  @click="downloadLicenseFile(lic.license_id)"
                >
                  <Icon name="download" size="xs" />
                  <span>Download .lic</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

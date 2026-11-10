<script setup lang="ts">
import { useCustomerAuth } from '~/composables/useCustomerAuth'
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'

definePageMeta({
  layout: 'customer',
})

const { profile, licenses, downloadLicenseFile } = useCustomerAuth()
</script>

<template>
  <div class="space-y-8">
    <!-- Welcome Banner -->
    <div class="p-8 rounded-3xl bg-gradient-to-r from-teal-900 via-slate-900 to-slate-900 text-white shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
      <div class="space-y-2">
        <span class="text-xs font-bold uppercase tracking-wider text-teal-400">Customer Account Console</span>
        <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight">Welcome, {{ profile.lab_name }}</h1>
        <p class="text-xs text-slate-300">
          Manage your offline Master PC software licences, Windows installer releases, tax invoices, and support tickets.
        </p>
      </div>

      <div class="flex items-center space-x-3">
        <NuxtLink to="/account/downloads">
          <Button variant="primary" size="sm" class="font-bold">
            <template #icon-left><Icon name="download" size="xs" /></template>
            Download v1.0.4 Installer
          </Button>
        </NuxtLink>
      </div>
    </div>

    <!-- Metrics Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
        <span class="text-xs font-semibold text-slate-500">Active Licences</span>
        <div class="text-2xl font-black text-slate-900 dark:text-white">{{ licenses.filter(l => l.status === 'ACTIVE').length }}</div>
        <span class="text-[11px] text-teal-600 font-bold">Hardware bound & verified</span>
      </div>

      <div class="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
        <span class="text-xs font-semibold text-slate-500">Primary Plan</span>
        <div class="text-2xl font-black text-slate-900 dark:text-white">Yearly Pro</div>
        <span class="text-[11px] text-slate-400">Valid until Nov 2027</span>
      </div>

      <div class="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
        <span class="text-xs font-semibold text-slate-500">LAN Workstations</span>
        <div class="text-2xl font-black text-slate-900 dark:text-white">Unlimited</div>
        <span class="text-[11px] text-emerald-600 font-bold">Local Hub Active</span>
      </div>

      <div class="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
        <span class="text-xs font-semibold text-slate-500">Support Level</span>
        <div class="text-2xl font-black text-slate-900 dark:text-white">Priority SLA</div>
        <span class="text-[11px] text-teal-600 font-bold">Phone & AnyDesk</span>
      </div>
    </div>

    <!-- Active Licences Quick Table -->
    <div class="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
      <div class="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <div>
          <h3 class="text-base font-bold text-slate-900 dark:text-white">Active Software Licences</h3>
          <p class="text-xs text-slate-500">Deploy these cryptographic keys on your Master PC</p>
        </div>
        <NuxtLink to="/account/licences" class="text-xs font-bold text-teal-600 hover:underline">
          View All & Re-Key →
        </NuxtLink>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead>
            <tr class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 font-semibold">
              <th class="py-3 px-6">Licence Key ID</th>
              <th class="py-3 px-6">Plan</th>
              <th class="py-3 px-6">Bound Machine ID</th>
              <th class="py-3 px-6">Valid Until</th>
              <th class="py-3 px-6">Status</th>
              <th class="py-3 px-6 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800/60">
            <tr v-for="lic in licenses" :key="lic.license_id" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
              <td class="py-3.5 px-6 font-mono font-bold text-slate-900 dark:text-white">{{ lic.license_id }}</td>
              <td class="py-3.5 px-6 font-medium">{{ lic.plan_code }}</td>
              <td class="py-3.5 px-6 font-mono text-slate-500">{{ lic.installation_id || 'Pending Activation' }}</td>
              <td class="py-3.5 px-6 text-slate-600 dark:text-slate-400">09 Nov 2027</td>
              <td class="py-3.5 px-6">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                  {{ lic.status }}
                </span>
              </td>
              <td class="py-3.5 px-6 text-right">
                <button
                  @click="downloadLicenseFile(lic.license_id)"
                  class="text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline flex items-center space-x-1 ml-auto"
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


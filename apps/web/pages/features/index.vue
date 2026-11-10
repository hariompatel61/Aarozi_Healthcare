<script setup lang="ts">
import { ref, computed } from 'vue'
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const searchQuery = ref('')
const selectedCategory = ref('All')

const categories = ['All', 'Patient & Front Desk', 'Diagnostic Reporting', 'Financial & Inventory', 'Operations & Compliance']

const features = [
  {
    category: 'Patient & Front Desk',
    name: 'Patient Registration & UHID',
    path: '/features/patient-management',
    desc: 'Rapid patient intake with Aadhaar/mobile auto-lookup, unique health identifier generation, and duplicate prevention.',
    icon: 'users',
  },
  {
    category: 'Patient & Front Desk',
    name: 'Barcode & Sample Tracking',
    path: '/features/barcode-management',
    desc: 'Thermal tube label printing with Code 128 / QR barcodes, color-coded tube guides, and phlebotomy tracking.',
    icon: 'qr-code',
  },
  {
    category: 'Patient & Front Desk',
    name: 'Offline & Local LAN Operations',
    path: '/features/offline-lan',
    desc: '100% operational survival without internet. Connect all reception, phlebotomy, and doctor desks over local LAN.',
    icon: 'shield',
  },
  {
    category: 'Diagnostic Reporting',
    name: 'Laboratory Reporting Engine',
    path: '/features/lab-reporting',
    desc: 'Configurable formats, age/gender normal ranges, panic value alerts, calculated parameters, and digital doctor signatures.',
    icon: 'beaker',
  },
  {
    category: 'Diagnostic Reporting',
    name: 'Radiology & Ultrasound Reporting',
    path: '/features/radiology-reporting',
    desc: 'Pre-built structured reporting templates for USG, Chest X-Ray, CT Brain, and ECG observations.',
    icon: 'document',
  },
  {
    category: 'Diagnostic Reporting',
    name: 'Tamper-Evident QR Reports',
    path: '/features/qr-reports',
    desc: 'Cryptographic QR codes on PDF reports allowing smartphone verification without exposing lab internal data.',
    icon: 'lock',
  },
  {
    category: 'Diagnostic Reporting',
    name: 'Test & Package Catalog Management',
    path: '/features/test-management',
    desc: 'Customizable test master, multi-tier health checkup packages, formulas, and automated calculation rules.',
    icon: 'cube',
  },
  {
    category: 'Financial & Inventory',
    name: 'Cashier Billing & Invoicing',
    path: '/features/billing',
    desc: 'GST compliant invoices, discount approval workflows, split payment modes, and daily cash counter reconciliation.',
    icon: 'shopping-cart',
  },
  {
    category: 'Financial & Inventory',
    name: 'Reagents & Inventory Control',
    path: '/features/inventory',
    desc: 'Automated reagent consumption deduction per test, lot numbers, kit tracking, and early expiry warnings.',
    icon: 'archive',
  },
  {
    category: 'Financial & Inventory',
    name: 'Expense Management & Petty Cash',
    path: '/features/expense-management',
    desc: 'Record daily lab expenses, courier fees, calibration logs, and utility payouts with cashier settlement integration.',
    icon: 'currency-rupee',
  },
  {
    category: 'Financial & Inventory',
    name: 'Business & Financial Analytics',
    path: '/features/business-analytics',
    desc: 'Daily collection charts, test volume trends, referral doctor commission ledgers, and revenue leak prevention.',
    icon: 'chart-bar',
  },
  {
    category: 'Operations & Compliance',
    name: 'Employee Roles & Permissions (RBAC)',
    path: '/features/employee-management',
    desc: 'Granular access controls separating receptionists, phlebotomists, lab technicians, and approving pathologists.',
    icon: 'user-group',
  },
  {
    category: 'Operations & Compliance',
    name: 'Data Export & Software Migration',
    path: '/features/data-migration',
    desc: 'Seamless migration assistant to import historical patient directories, doctor contacts, and test lists from Excel/CSV.',
    icon: 'arrow-down-tray',
  },
  {
    category: 'Operations & Compliance',
    name: 'Automated Backup & Disaster Recovery',
    path: '/features/backup-restore',
    desc: 'Scheduled 1-click encrypted backups to local secondary drives, USB storage, or customer-owned cloud storage.',
    icon: 'arrow-path',
  },
]

const filteredFeatures = computed(() => {
  return features.filter((f) => {
    const matchesCat = selectedCategory.value === 'All' || f.category === selectedCategory.value
    const matchesSearch =
      !searchQuery.value.trim() ||
      f.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      f.desc.toLowerCase().includes(searchQuery.value.toLowerCase())
    return matchesCat && matchesSearch
  })
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300 border border-teal-200">
        Feature Directory
      </span>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Everything Your Laboratory Needs to Operate Flawlessly
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Explore detailed capabilities across pre-analytical, analytical, post-analytical, financial, and administrative operations.
      </p>
    </div>

    <!-- Filter & Search Bar -->
    <div class="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
      <div class="flex flex-wrap gap-2">
        <button
          v-for="cat in categories"
          :key="cat"
          type="button"
          class="px-3.5 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer"
          :class="[
            selectedCategory === cat
              ? 'bg-teal-600 text-white'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
          ]"
          @click="selectedCategory = cat"
        >
          {{ cat }}
        </button>
      </div>

      <div class="w-full sm:w-72">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search features (e.g. barcode, GST, QR)..."
          class="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
        />
      </div>
    </div>

    <!-- Feature Cards Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <NuxtLink
        v-for="f in filteredFeatures"
        :key="f.path"
        :to="f.path"
        class="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-500 hover:shadow-lg transition-all space-y-3 group flex flex-col justify-between"
      >
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
              {{ f.category }}
            </span>
            <Icon name="arrow-right" size="xs" class="text-slate-400 group-hover:text-teal-600 group-hover:translate-x-1 transition-all" />
          </div>

          <h3 class="text-base font-bold text-slate-900 dark:text-white group-hover:text-teal-600 transition-colors">
            {{ f.name }}
          </h3>

          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            {{ f.desc }}
          </p>
        </div>

        <span class="text-xs font-bold text-teal-600 inline-block pt-3 border-t border-slate-100 dark:border-slate-800">
          Learn More &rarr;
        </span>
      </NuxtLink>
    </div>

    <CtaBanner />
  </div>
</template>

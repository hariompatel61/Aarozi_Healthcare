<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useTheme } from '~/composables/useTheme'
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'

const { isDark, toggleTheme } = useTheme()
const isMobileOpen = ref(false)
const activeDropdown = ref<string | null>(null)

function toggleDropdown(name: string) {
  activeDropdown.value = activeDropdown.value === name ? null : name
}

function closeDropdowns() {
  activeDropdown.value = null
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    closeDropdowns()
    isMobileOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

const featureCategories = [
  {
    category: 'Patient & Front Desk',
    items: [
      { name: 'Patient Registration & UHID', path: '/features/patient-management', desc: 'Demographics, duplicate prevention, quick intake' },
      { name: 'Barcode & Sample Tracking', path: '/features/barcode-management', desc: 'Thermal tube labels, collection to disposal audit' },
      { name: 'Offline & Local LAN', path: '/features/offline-lan', desc: '100% operational survival without internet connectivity' },
    ],
  },
  {
    category: 'Diagnostic Reporting',
    items: [
      { name: 'Laboratory Reporting', path: '/features/lab-reporting', desc: 'Configurable formats, abnormal flags, delta checks' },
      { name: 'Radiology Reporting', path: '/features/radiology-reporting', desc: 'Ultrasound, X-Ray, CT findings & impression templates' },
      { name: 'Tamper-Evident QR Reports', path: '/features/qr-reports', desc: 'Instant cryptographic patient PDF report verification' },
      { name: 'Test & Package Catalog', path: '/features/test-management', desc: 'Automated calculations, formulas, multi-tier panels' },
    ],
  },
  {
    category: 'Financial & Inventory',
    items: [
      { name: 'Billing & GST Invoicing', path: '/features/billing', desc: 'Split payments, doctor commission ledger, cashier audit' },
      { name: 'Reagents & Inventory', path: '/features/inventory', desc: 'Lot tracking, automated consumption per test, expiry alerts' },
      { name: 'Expense & Petty Cash', path: '/features/expense-management', desc: 'Daily operational expenses, courier fees, payouts' },
      { name: 'Business Analytics', path: '/features/business-analytics', desc: 'Revenue breakdowns, test volumes, partner payouts' },
    ],
  },
  {
    category: 'Operations & Compliance',
    items: [
      { name: 'Roles & Staff Permissions', path: '/features/employee-management', desc: 'Reception, Phlebotomy, Tech, Pathologist RBAC' },
      { name: 'Data Export & Migration', path: '/features/data-migration', desc: 'Seamless migration from legacy laboratory software' },
      { name: 'Automated Backup & Restore', path: '/features/backup-restore', desc: '1-click encrypted local & external drive backup' },
    ],
  },
]

const solutionItems = [
  { name: 'Pathology Laboratories', path: '/solutions/pathology-lab', desc: 'Standalone clinical biochemistry, hematology & microbiology labs', icon: 'beaker' },
  { name: 'Integrated Diagnostic Centres', path: '/solutions/diagnostic-centre', desc: 'Combined Pathology + Radiology + Ultrasound imaging setups', icon: 'cube' },
  { name: 'Radiology & Imaging Centres', path: '/solutions/radiology-centre', desc: 'Structured reporting for CT, MRI, Ultrasound, and X-Ray', icon: 'document' },
  { name: 'Blood Banks & Transfusion Hubs', path: '/solutions/blood-bank', desc: 'Donor screening, TTI testing, cross-matching, cold inventory', icon: 'shield' },
]

const resourceItems = [
  { name: 'Report Format Library', path: '/report-formats', desc: 'Browse 50+ NABL-aligned diagnostic templates' },
  { name: 'Software Downloads', path: '/download', desc: 'Windows desktop installer v1.0.4 & release notes' },
  { name: 'Setup & Installation Guide', path: '/support', desc: 'Step-by-step master PC & LAN configuration' },
  { name: 'Customer Success Stories', path: '/success-stories', desc: 'Real case studies of diagnostic transformations' },
  { name: 'Frequently Asked Questions', path: '/faq', desc: 'Everything about offline mode, licensing & data privacy' },
  { name: 'Clinical & Lab Blog', path: '/blog', desc: 'Industry guides on NABL audits & lab profitability' },
]
</script>

<template>
  <header class="sticky top-0 z-50 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between">
      <!-- Logo Branding -->
      <NuxtLink to="/" class="flex items-center space-x-3 group" @click="closeDropdowns">
        <div class="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center font-black text-lg shadow-md group-hover:bg-teal-700 transition-colors">
          AH
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <span class="font-extrabold text-lg tracking-tight text-slate-900 dark:text-white">Aarozi Healthcare</span>
            <span class="hidden sm:inline-block px-2 py-0.5 text-[10px] font-bold bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300 rounded-full border border-teal-200 dark:border-teal-800 uppercase tracking-wide">
              LIS v1.0.4
            </span>
          </div>
          <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium tracking-tight">Offline-First Diagnostic & Blood Bank Software</p>
        </div>
      </NuxtLink>

      <!-- Desktop Navigation Links with Mega-Dropdowns -->
      <nav class="hidden lg:flex items-center space-x-1 text-sm font-semibold text-slate-700 dark:text-slate-200">
        <!-- Home -->
        <NuxtLink to="/" class="px-3 py-2 rounded-lg hover:text-teal-600 dark:hover:text-teal-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors" @click="closeDropdowns">
          Home
        </NuxtLink>

        <!-- Product Overview -->
        <NuxtLink to="/product" class="px-3 py-2 rounded-lg hover:text-teal-600 dark:hover:text-teal-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors" @click="closeDropdowns">
          Product
        </NuxtLink>

        <!-- Features Mega-Dropdown -->
        <div class="relative" @mouseleave="closeDropdowns">
          <button
            type="button"
            class="px-3 py-2 rounded-lg hover:text-teal-600 dark:hover:text-teal-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors inline-flex items-center space-x-1"
            :class="{ 'text-teal-600 dark:text-teal-400 bg-slate-50 dark:bg-slate-800': activeDropdown === 'features' }"
            @click="toggleDropdown('features')"
            @mouseenter="activeDropdown = 'features'"
          >
            <span>Features</span>
            <Icon name="chevron-down" size="xs" :class="{ 'rotate-180': activeDropdown === 'features' }" class="transition-transform duration-200" />
          </button>

          <!-- Features Dropdown Panel -->
          <div
            v-if="activeDropdown === 'features'"
            class="absolute top-full left-1/2 -translate-x-1/2 w-[880px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-6 grid grid-cols-4 gap-6 animate-in fade-in slide-in-from-top-2 duration-150 z-50 mt-1"
          >
            <div v-for="cat in featureCategories" :key="cat.category" class="space-y-3">
              <h4 class="text-xs font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400 border-b border-slate-100 dark:border-slate-800 pb-1.5">
                {{ cat.category }}
              </h4>
              <ul class="space-y-2">
                <li v-for="item in cat.items" :key="item.path">
                  <NuxtLink
                    :to="item.path"
                    class="block p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors group"
                    @click="closeDropdowns"
                  >
                    <div class="text-xs font-bold text-slate-900 dark:text-white group-hover:text-teal-600 transition-colors">
                      {{ item.name }}
                    </div>
                    <div class="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-1">
                      {{ item.desc }}
                    </div>
                  </NuxtLink>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Solutions Dropdown -->
        <div class="relative" @mouseleave="closeDropdowns">
          <button
            type="button"
            class="px-3 py-2 rounded-lg hover:text-teal-600 dark:hover:text-teal-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors inline-flex items-center space-x-1"
            :class="{ 'text-teal-600 dark:text-teal-400 bg-slate-50 dark:bg-slate-800': activeDropdown === 'solutions' }"
            @click="toggleDropdown('solutions')"
            @mouseenter="activeDropdown = 'solutions'"
          >
            <span>Solutions</span>
            <Icon name="chevron-down" size="xs" :class="{ 'rotate-180': activeDropdown === 'solutions' }" class="transition-transform duration-200" />
          </button>

          <!-- Solutions Dropdown Panel -->
          <div
            v-if="activeDropdown === 'solutions'"
            class="absolute top-full left-0 w-84 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-4 space-y-2 animate-in fade-in slide-in-from-top-2 duration-150 z-50 mt-1"
          >
            <NuxtLink
              v-for="item in solutionItems"
              :key="item.path"
              :to="item.path"
              class="block p-3 rounded-xl hover:bg-teal-50/60 dark:hover:bg-slate-800 transition-colors group"
              @click="closeDropdowns"
            >
              <div class="text-xs font-bold text-slate-900 dark:text-white group-hover:text-teal-600">
                {{ item.name }}
              </div>
              <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                {{ item.desc }}
              </div>
            </NuxtLink>
          </div>
        </div>

        <!-- Report Formats -->
        <NuxtLink to="/report-formats" class="px-3 py-2 rounded-lg hover:text-teal-600 dark:hover:text-teal-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors" @click="closeDropdowns">
          Report Formats
        </NuxtLink>

        <!-- Pricing -->
        <NuxtLink to="/pricing" class="px-3 py-2 rounded-lg hover:text-teal-600 dark:hover:text-teal-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors" @click="closeDropdowns">
          Pricing
        </NuxtLink>

        <!-- Resources Dropdown -->
        <div class="relative" @mouseleave="closeDropdowns">
          <button
            type="button"
            class="px-3 py-2 rounded-lg hover:text-teal-600 dark:hover:text-teal-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors inline-flex items-center space-x-1"
            :class="{ 'text-teal-600 dark:text-teal-400 bg-slate-50 dark:bg-slate-800': activeDropdown === 'resources' }"
            @click="toggleDropdown('resources')"
            @mouseenter="activeDropdown = 'resources'"
          >
            <span>Resources</span>
            <Icon name="chevron-down" size="xs" :class="{ 'rotate-180': activeDropdown === 'resources' }" class="transition-transform duration-200" />
          </button>

          <!-- Resources Dropdown Panel -->
          <div
            v-if="activeDropdown === 'resources'"
            class="absolute top-full right-0 w-84 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-4 space-y-2 animate-in fade-in slide-in-from-top-2 duration-150 z-50 mt-1"
          >
            <NuxtLink
              v-for="item in resourceItems"
              :key="item.path"
              :to="item.path"
              class="block p-3 rounded-xl hover:bg-teal-50/60 dark:hover:bg-slate-800 transition-colors group"
              @click="closeDropdowns"
            >
              <div class="text-xs font-bold text-slate-900 dark:text-white group-hover:text-teal-600">
                {{ item.name }}
              </div>
              <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                {{ item.desc }}
              </div>
            </NuxtLink>
          </div>
        </div>

        <!-- About Us -->
        <NuxtLink to="/about" class="px-3 py-2 rounded-lg hover:text-teal-600 dark:hover:text-teal-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors" @click="closeDropdowns">
          About
        </NuxtLink>

        <!-- Contact -->
        <NuxtLink to="/contact" class="px-3 py-2 rounded-lg hover:text-teal-600 dark:hover:text-teal-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors" @click="closeDropdowns">
          Contact
        </NuxtLink>
      </nav>

      <!-- Right Action Buttons -->
      <div class="hidden sm:flex items-center space-x-3">
        <!-- Theme Switcher Button -->
        <button
          type="button"
          class="p-2 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
          :title="isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme'"
          aria-label="Toggle theme"
          @click="toggleTheme"
        >
          <Icon :name="isDark ? 'sun' : 'moon'" size="sm" />
        </button>

        <!-- Login Button -->
        <NuxtLink to="/login">
          <Button variant="secondary" size="sm">
            <template #icon-left><Icon name="lock" size="xs" /></template>
            Login
          </Button>
        </NuxtLink>

        <!-- Primary CTA: Get Started / Buy Licence -->
        <NuxtLink to="/pricing">
          <Button variant="primary" size="sm">
            Buy Licence / Trial
          </Button>
        </NuxtLink>
      </div>

      <!-- Mobile Hamburger Button -->
      <button
        type="button"
        class="lg:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
        aria-label="Toggle navigation menu"
        @click="isMobileOpen = !isMobileOpen"
      >
        <Icon :name="isMobileOpen ? 'x' : 'menu'" size="md" />
      </button>
    </div>

    <!-- Mobile Drawer Navigation -->
    <div
      v-if="isMobileOpen"
      class="lg:hidden fixed inset-x-0 top-18 bottom-0 bg-white dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 p-6 overflow-y-auto space-y-6 z-50"
    >
      <div class="space-y-2">
        <NuxtLink to="/" class="block px-3 py-2 rounded-lg text-sm font-bold text-slate-800 dark:text-slate-200" @click="isMobileOpen = false">
          Home
        </NuxtLink>
        <NuxtLink to="/product" class="block px-3 py-2 rounded-lg text-sm font-bold text-slate-800 dark:text-slate-200" @click="isMobileOpen = false">
          Product Architecture
        </NuxtLink>
        <NuxtLink to="/features" class="block px-3 py-2 rounded-lg text-sm font-bold text-teal-600" @click="isMobileOpen = false">
          Explore All Features &rarr;
        </NuxtLink>
        <NuxtLink to="/report-formats" class="block px-3 py-2 rounded-lg text-sm font-bold text-slate-800 dark:text-slate-200" @click="isMobileOpen = false">
          Report Formats
        </NuxtLink>
        <NuxtLink to="/pricing" class="block px-3 py-2 rounded-lg text-sm font-bold text-slate-800 dark:text-slate-200" @click="isMobileOpen = false">
          Pricing & Plans
        </NuxtLink>
        <NuxtLink to="/download" class="block px-3 py-2 rounded-lg text-sm font-bold text-slate-800 dark:text-slate-200" @click="isMobileOpen = false">
          Download Windows Installer
        </NuxtLink>
        <NuxtLink to="/faq" class="block px-3 py-2 rounded-lg text-sm font-bold text-slate-800 dark:text-slate-200" @click="isMobileOpen = false">
          FAQs
        </NuxtLink>
        <NuxtLink to="/about" class="block px-3 py-2 rounded-lg text-sm font-bold text-slate-800 dark:text-slate-200" @click="isMobileOpen = false">
          About Us
        </NuxtLink>
        <NuxtLink to="/contact" class="block px-3 py-2 rounded-lg text-sm font-bold text-slate-800 dark:text-slate-200" @click="isMobileOpen = false">
          Contact Sales & Support
        </NuxtLink>
      </div>

      <div class="pt-6 border-t border-slate-200 dark:border-slate-800 flex flex-col space-y-3">
        <NuxtLink to="/login" class="w-full" @click="isMobileOpen = false">
          <Button variant="secondary" size="md" class="w-full justify-center">
            Login
          </Button>
        </NuxtLink>
        <NuxtLink to="/pricing" class="w-full" @click="isMobileOpen = false">
          <Button variant="primary" size="md" class="w-full justify-center">
            Get Started & Buy Licence
          </Button>
        </NuxtLink>
      </div>
    </div>
  </header>
</template>


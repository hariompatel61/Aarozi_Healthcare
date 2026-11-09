<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

interface Props {
  collapsed?: boolean
  mobileOpen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  collapsed: false,
  mobileOpen: false,
})

const emit = defineEmits<{
  (e: 'update:collapsed', val: boolean): void
  (e: 'close-mobile'): void
}>()

const route = useRoute()
const menuSearch = ref('')

// Accordion collapse state per group
const groupOpen = ref<Record<string, boolean>>({
  frontDesk: true,
  labOps: true,
  finance: true,
  settings: true,
  specialty: false,
})

function toggleGroup(group: string) {
  groupOpen.value[group] = !groupOpen.value[group]
}

interface NavItem {
  name: string
  to: string
  href: string
  icon: string
  badge?: string
  exact?: boolean
}

interface NavGroup {
  id: string
  title: string
  items: NavItem[]
}

const navigationGroups: NavGroup[] = [
  {
    id: 'frontDesk',
    title: 'Front Desk & Intake',
    items: [
      { name: 'Patient Directory', to: '/patients', href: '/patients', icon: 'users', exact: true },
      { name: 'Intake & Registration', to: '/patients/register', href: '/patients/register', icon: 'clipboard-check', badge: 'New UHID' },
    ],
  },
  {
    id: 'labOps',
    title: 'Clinical Laboratory (LIS)',
    items: [
      { name: 'Worklist & Analyte Entry', to: '/pathology/results', href: '/pathology/results', icon: 'document-report', badge: 'Results' },
      { name: 'Sample Tracking & Barcodes', to: '/pathology/samples', href: '/pathology/samples', icon: 'beaker' },
      { name: 'Pathologist Verification', to: '/pathology/verification', href: '/pathology/verification', icon: 'shield-check', badge: 'Sign-off' },
      { name: 'Report Release Desk', to: '/reporting/release', href: '/reporting/release', icon: 'document-report', badge: 'QR PDF' },
    ],
  },
  {
    id: 'finance',
    title: 'Finance & B2B Partners',
    items: [
      { name: 'Invoices & Cashier', to: '/billing/invoices', href: '/billing/invoices', icon: 'credit-card', badge: 'POS' },
      { name: 'Referral Doctors & Centers', to: '/billing/referrals', href: '/billing/referrals', icon: 'briefcase' },
    ],
  },
  {
    id: 'specialty',
    title: 'Blood Bank & Transfusion',
    items: [
      { name: 'Donor Registry', to: '/blood_bank/donors', href: '/blood_bank/donors', icon: 'heart' },
      { name: 'Blood Component Inventory', to: '/blood_bank/inventory', href: '/blood_bank/inventory', icon: 'archive' },
      { name: 'Compatibility & Cross-Match', to: '/blood_bank/crossmatch', href: '/blood_bank/crossmatch', icon: 'heart' },
    ],
  },
  {
    id: 'settings',
    title: 'Platform & Settings',
    items: [
      { name: 'Test Catalog Master', to: '/pathology/catalog', href: '/pathology/catalog', icon: 'archive', badge: '1000+' },
      { name: 'Analyzer Interfacing', to: '/pathology/instruments', href: '/pathology/instruments', icon: 'beaker', badge: 'ASTM/HL7' },
      { name: 'Visual Template Studio', to: '/reporting/designer', href: '/reporting/designer', icon: 'document-report', badge: 'Studio' },
      { name: 'Report Themes Gallery', to: '/reporting/templates', href: '/reporting/templates', icon: 'document-report' },
      { name: 'Integrations & Cloud', to: '/admin/integrations', href: '/admin/integrations', icon: 'share', badge: 'WhatsApp' },
      { name: 'Offline & Cloud Sync', to: '/admin/sync', href: '/admin/sync', icon: 'cloud', badge: 'Hybrid' },
      { name: 'System Licensing', to: '/admin/licensing', href: '/admin/licensing', icon: 'cog', badge: 'Ed25519' },
      { name: 'Staff & Access Control', to: '/admin/users', href: '/admin/users', icon: 'users' },
    ],
  },
]

// Active pathname comparison with strict exact matching for /patients vs /patients/register:
// const isActive = item.exact ? pathname === item.href : pathname.startsWith(item.href);
function isActive(item: NavItem | string, exact?: boolean) {
  if (!route) return false
  const pathname = route.path
  if (typeof item === 'string') {
    if (item === '/dashboard') return pathname === '/dashboard' || pathname === '/'
    const isExact = exact !== undefined ? exact : item === '/patients'
    return isExact ? pathname === item : pathname.startsWith(item)
  }
  const href = item.href || item.to
  if (href === '/dashboard') return pathname === '/dashboard' || pathname === '/'
  const isExact = item.exact !== undefined ? item.exact : href === '/patients'
  return isExact ? pathname === href : pathname.startsWith(href)
}

onMounted(() => {
  // Auto-expand group that contains active route
  navigationGroups.forEach((g) => {
    if (g.items.some((itm) => isActive(itm))) {
      groupOpen.value[g.id] = true
    }
  })
})

const filteredGroups = computed(() => {
  const q = menuSearch.value.trim().toLowerCase()
  if (!q) return navigationGroups

  return navigationGroups
    .map((g) => ({
      ...g,
      items: g.items.filter((itm) => itm.name.toLowerCase().includes(q)),
    }))
    .filter((g) => g.items.length > 0)
})
</script>

<template>
  <div>
    <!-- Mobile Drawer Backdrop -->
    <div
      v-if="mobileOpen"
      class="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs lg:hidden"
      @click="emit('close-mobile')"
    />

    <!-- Sidebar Container (Minimal White & Medical Clinical Theme) -->
    <aside
      :class="[
        'fixed inset-y-0 left-0 z-40 bg-white text-slate-700 transition-all duration-200 flex flex-col border-r border-slate-200 select-none shadow-xs',
        collapsed ? 'w-16' : 'w-56',
        mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      ]"
    >
      <!-- Brand Header -->
      <div class="h-14 flex items-center justify-between px-4 border-b border-slate-200 shrink-0 bg-white">
        <NuxtLink to="/dashboard" class="flex items-center space-x-2.5 overflow-hidden group">
          <div class="h-8 w-8 rounded-lg bg-sky-50 border border-sky-100 flex items-center justify-center shrink-0">
            <svg class="h-5 w-5 text-sky-600 fill-current drop-shadow-2xs" viewBox="0 0 24 24">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
          </div>
          <div v-if="!collapsed" class="truncate text-left">
            <span class="font-bold text-slate-900 tracking-tight text-sm block font-sans">Aarozi</span>
            <span class="text-[9px] text-sky-700 font-semibold block -mt-0.5 tracking-wider uppercase">Healthcare LIS</span>
          </div>
        </NuxtLink>

        <!-- Collapse Toggle (Desktop) -->
        <button
          v-if="!collapsed"
          type="button"
          class="hidden lg:flex p-1 text-slate-400 hover:text-slate-700 rounded-md hover:bg-slate-100 cursor-pointer transition"
          title="Collapse Sidebar"
          @click="emit('update:collapsed', true)"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>

      <!-- Sidebar Menu Filter -->
      <div v-if="!collapsed" class="px-3 pt-2.5 pb-1 shrink-0">
        <div class="relative">
          <span class="absolute inset-y-0 left-0 flex items-center pl-2.5 text-slate-400 pointer-events-none">
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <input
            v-model="menuSearch"
            type="text"
            placeholder="Filter menus..."
            class="input-faang w-full pl-8 pr-7 py-1 text-xs"
          />
          <button
            v-if="menuSearch"
            type="button"
            class="absolute inset-y-0 right-0 flex items-center pr-2 text-slate-400 hover:text-slate-600 cursor-pointer"
            title="Clear"
            @click="menuSearch = ''"
          >
            <span class="text-sm leading-none">&times;</span>
          </button>
        </div>
      </div>

      <!-- Navigation Content -->
      <nav class="flex-1 overflow-y-auto px-2 py-2 space-y-2 text-left">
        <!-- Dashboard Top Item -->
        <NuxtLink
          to="/dashboard"
          :title="collapsed ? 'Dashboard' : undefined"
          :class="[
            'flex items-center text-xs font-medium px-2.5 py-2 transition-all group relative',
            isActive('/dashboard')
              ? 'bg-sky-50 text-sky-700 font-semibold border-l-4 border-sky-600 rounded-r-lg'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 rounded-lg'
          ]"
          @click="emit('close-mobile')"
        >
          <span class="h-4 w-4 shrink-0 flex items-center justify-center mr-2.5" :class="isActive('/dashboard') ? 'text-sky-600' : 'text-slate-400 group-hover:text-slate-700'">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </span>
          <span v-if="!collapsed" class="truncate flex-1">Overview Dashboard</span>
        </NuxtLink>

        <!-- 4 Collapsible Accordion Navigation Groups -->
        <div v-for="group in filteredGroups" :key="group.id" class="space-y-0.5">
          <!-- Accordion Header -->
          <div
            v-if="!collapsed"
            class="flex items-center justify-between px-2 pt-2.5 pb-1 text-[10px] font-semibold tracking-wider text-slate-400 uppercase cursor-pointer hover:text-slate-700 transition"
            @click="toggleGroup(group.id)"
          >
            <span class="truncate">{{ group.title }}</span>
            <svg
              class="h-3 w-3 transform transition-transform duration-150 text-slate-400"
              :class="groupOpen[group.id] ? 'rotate-180' : ''"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          <div v-else class="my-1 border-t border-slate-100" />

          <!-- Group Links -->
          <div v-show="collapsed || groupOpen[group.id]" class="space-y-0.5">
            <NuxtLink
              v-for="item in group.items"
              :key="item.to"
              :to="item.to"
              :title="collapsed ? item.name : undefined"
              :class="[
                'flex items-center text-xs font-medium px-2.5 py-1.5 transition-all group relative',
                isActive(item)
                  ? 'bg-sky-50 text-sky-700 font-semibold border-l-4 border-sky-600 rounded-r-lg'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 rounded-lg'
              ]"
              @click="emit('close-mobile')"
            >
              <span class="h-4 w-4 shrink-0 flex items-center justify-center mr-2.5" :class="isActive(item) ? 'text-sky-600' : 'text-slate-400 group-hover:text-slate-700'">
                <!-- Users / Directory -->
                <svg v-if="item.icon === 'users'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                <!-- Clipboard / POS -->
                <svg v-else-if="item.icon === 'clipboard-check'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
                <!-- Samples / Beaker -->
                <svg v-else-if="item.icon === 'beaker'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
                <!-- Billing / Credit Card -->
                <svg v-else-if="item.icon === 'credit-card'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
                <!-- Document / Reports -->
                <svg v-else-if="item.icon === 'document-report'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <!-- Doctors / Briefcase -->
                <svg v-else-if="item.icon === 'briefcase'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <!-- Shield / Approvals -->
                <svg v-else-if="item.icon === 'shield-check'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <!-- Heart / Blood Bank -->
                <svg v-else-if="item.icon === 'heart'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
                <!-- Catalog / Archive -->
                <svg v-else-if="item.icon === 'archive'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
                <!-- Integrations / Share -->
                <svg v-else-if="item.icon === 'share'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
                <!-- Cloud / Sync -->
                <svg v-else-if="item.icon === 'cloud'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z" />
                </svg>
                <!-- Settings / Cog -->
                <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </span>

              <span v-if="!collapsed" class="truncate flex-1 text-xs">
                {{ item.name }}
              </span>

              <!-- Optional Pill Badge -->
              <span
                v-if="!collapsed && item.badge"
                class="ml-auto text-[9px] font-mono px-1.5 py-0.2 rounded bg-sky-100 text-sky-700 font-semibold border border-sky-200"
              >
                {{ item.badge }}
              </span>
            </NuxtLink>
          </div>
        </div>
      </nav>

      <!-- Expand Button when collapsed -->
      <div v-if="collapsed" class="p-2 border-t border-slate-200 hidden lg:block">
        <button
          type="button"
          class="w-full py-2 flex items-center justify-center text-slate-400 hover:text-slate-700 rounded-md hover:bg-slate-100 cursor-pointer transition"
          title="Expand Sidebar"
          @click="emit('update:collapsed', false)"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      <!-- Footer Info: "Local Server Online v1.0.0" -->
      <div v-if="!collapsed" class="p-3 border-t border-slate-200 text-[11px] text-slate-500 text-left bg-slate-50/80">
        <div class="flex items-center space-x-2">
          <span class="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span class="font-medium text-slate-700">Local Server Online</span>
        </div>
        <p class="text-[10px] text-slate-400 mt-0.5 font-mono">v1.0.0 &bull; Relational SQLite</p>
      </div>
    </aside>
  </div>
</template>

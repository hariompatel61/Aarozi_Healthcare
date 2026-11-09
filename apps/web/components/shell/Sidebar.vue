<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon, { type IconName } from '~/components/ui/Icon.vue'
import Kbd from '~/components/ui/Kbd.vue'
import IconButton from '~/components/ui/IconButton.vue'

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
const router = useRouter()

// User session state
const staffUser = ref<{ username?: string; station?: string; branch?: string }>({})

onMounted(() => {
  if (typeof window !== 'undefined') {
    try {
      const stored = localStorage.getItem('aarozi_user')
      if (stored) {
        staffUser.value = JSON.parse(stored)
      }
    } catch (e) {
      console.warn('Failed parsing aarozi_user', e)
    }
  }
})

function handleLogout() {
  const authCookie = useCookie('auth_token', { path: '/' })
  const userCookie = useCookie('aarozi_user', { path: '/' })
  authCookie.value = null
  userCookie.value = null

  if (typeof window !== 'undefined') {
    localStorage.removeItem('token')
    localStorage.removeItem('access_token')
    localStorage.removeItem('aarozi_user')
  }
  router.push('/login')
}

interface NavItem {
  name: string
  to: string
  icon: IconName
  shortcut?: string
  badgeCount?: number
}

interface NavSection {
  title: string
  items: NavItem[]
}

const navSections: NavSection[] = [
  {
    title: 'Core Workflow',
    items: [
      { name: 'Dashboard', to: '/dashboard', icon: 'activity' },
      { name: 'Registration', to: '/patients/register', icon: 'user', shortcut: 'F2' },
      { name: 'Patient Directory', to: '/patients', icon: 'users' },
    ],
  },
  {
    title: 'Laboratory Ops',
    items: [
      { name: 'Worklist & Results', to: '/pathology/results', icon: 'file-text' },
      { name: 'Sample Tracking', to: '/pathology/samples', icon: 'beaker' },
      { name: 'Pathologist Verification', to: '/pathology/verification', icon: 'shield-check' },
      { name: 'Report Release Desk', to: '/reporting/release', icon: 'printer' },
      { name: 'Blood Bank', to: '/blood_bank/inventory', icon: 'heart' },
    ],
  },
  {
    title: 'Billing & Settings',
    items: [
      { name: 'Invoices & POS', to: '/billing/invoices', icon: 'credit-card' },
      { name: 'Referral Doctors', to: '/billing/referrals', icon: 'briefcase' },
      { name: 'Settings Hub', to: '/admin/users', icon: 'settings' },
    ],
  },
]

function isCurrentRoute(path: string): boolean {
  if (path === '/dashboard') {
    return route.path === '/dashboard'
  }
  return route.path.startsWith(path)
}
</script>

<template>
  <div>
    <!-- Mobile Backdrop -->
    <div
      v-if="mobileOpen"
      class="fixed inset-0 z-40 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-2xs lg:hidden"
      aria-hidden="true"
      @click="emit('close-mobile')"
    />

    <!-- Main Sidebar Shell -->
    <aside
      :class="[
        'fixed top-0 bottom-0 left-0 z-40 flex flex-col bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 transition-all duration-200 select-none text-left',
        collapsed ? 'w-16' : 'w-56',
        mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      ]"
    >
      <!-- Top Brand Header -->
      <div class="h-14 flex items-center justify-between px-3.5 border-b border-slate-100 dark:border-slate-800 shrink-0">
        <NuxtLink to="/dashboard" class="flex items-center space-x-2.5 min-w-0" @click="emit('close-mobile')">
          <div class="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center font-bold text-sm shrink-0 shadow-xs">
            AH
          </div>
          <div v-if="!collapsed" class="truncate">
            <div class="font-bold text-xs tracking-tight text-slate-900 dark:text-white">Aarozi Healthcare</div>
            <div class="text-[10px] text-teal-600 dark:text-teal-400 font-medium">Pathology LIS</div>
          </div>
        </NuxtLink>

        <!-- Desktop Collapse Toggle Button -->
        <button
          v-if="!collapsed"
          type="button"
          class="hidden lg:flex p-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          title="Collapse navigation"
          @click="emit('update:collapsed', true)"
        >
          <Icon name="chevron-left" size="xs" />
        </button>

        <button
          v-else
          type="button"
          class="hidden lg:flex mx-auto p-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          title="Expand navigation"
          @click="emit('update:collapsed', false)"
        >
          <Icon name="chevron-right" size="xs" />
        </button>

        <!-- Mobile Close Button -->
        <button
          type="button"
          class="lg:hidden p-1 text-slate-400 hover:text-slate-700 rounded-md"
          @click="emit('close-mobile')"
        >
          <Icon name="x" size="sm" />
        </button>
      </div>

      <!-- Navigation Links Container -->
      <nav class="flex-1 overflow-y-auto px-2 py-3 space-y-4 no-scrollbar">
        <div v-for="sec in navSections" :key="sec.title" class="space-y-1">
          <!-- Section Heading (Only when expanded) -->
          <div
            v-if="!collapsed"
            class="px-2.5 pb-1 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider"
          >
            {{ sec.title }}
          </div>

          <!-- Section Items -->
          <NuxtLink
            v-for="item in sec.items"
            :key="item.to"
            :to="item.to"
            :title="collapsed ? item.name : undefined"
            :class="[
              'group flex items-center rounded-lg transition-colors duration-150',
              collapsed ? 'justify-center p-2' : 'px-2.5 py-1.5 justify-between',
              isCurrentRoute(item.to)
                ? 'bg-teal-50 dark:bg-teal-950/60 text-teal-800 dark:text-teal-200 font-semibold'
                : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60'
            ]"
            @click="emit('close-mobile')"
          >
            <div class="flex items-center space-x-2.5 min-w-0">
              <Icon
                :name="item.icon"
                size="sm"
                :class="[
                  'shrink-0 transition-colors',
                  isCurrentRoute(item.to) ? 'text-teal-600 dark:text-teal-400' : 'text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200'
                ]"
              />
              <span v-if="!collapsed" class="text-xs truncate">
                {{ item.name }}
              </span>
            </div>

            <!-- Keyboard shortcut hint -->
            <Kbd v-if="!collapsed && item.shortcut" size="xs">
              {{ item.shortcut }}
            </Kbd>
          </NuxtLink>
        </div>
      </nav>

      <!-- Bottom Staff Profile & Logout Footer -->
      <div class="p-2.5 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 shrink-0">
        <div v-if="!collapsed" class="flex items-center justify-between">
          <div class="min-w-0 pr-1">
            <div class="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
              {{ staffUser.username || 'Staff User' }}
            </div>
            <div class="text-[10px] text-slate-400 truncate">
              {{ staffUser.station || 'Front-Office' }}
            </div>
          </div>
          <button
            type="button"
            class="p-1.5 text-slate-400 hover:text-red-600 dark:hover:text-red-400 rounded-md hover:bg-red-50 dark:hover:bg-red-950/50 transition-colors cursor-pointer"
            title="Lock / Sign Out"
            @click="handleLogout"
          >
            <Icon name="lock" size="xs" />
          </button>
        </div>

        <div v-else class="flex justify-center">
          <button
            type="button"
            class="p-1.5 text-slate-400 hover:text-red-600 rounded-md hover:bg-red-50"
            title="Lock / Sign Out"
            @click="handleLogout"
          >
            <Icon name="lock" size="xs" />
          </button>
        </div>
      </div>
    </aside>
  </div>
</template>

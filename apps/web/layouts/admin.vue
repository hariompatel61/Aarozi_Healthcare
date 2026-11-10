<script setup lang="ts">
import { ref } from 'vue'
import { useAdminAuth } from '~/composables/useAdminAuth'
import { useTheme } from '~/composables/useTheme'
import ToastProvider from '~/components/ui/ToastProvider.vue'
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'

const { currentAdmin, logout } = useAdminAuth()
const { isDark, toggleTheme } = useTheme()
const route = useRoute()
const router = useRouter()

const adminNavItems = [
  { id: 'plans', name: 'Subscription Plans', icon: 'tag', desc: 'Pricing, quotas & feature packages' },
  { id: 'labs', name: 'Diagnostic Labs', icon: 'building', desc: 'Tenant laboratories & active instances' },
  { id: 'license-gen', name: 'License Generator', icon: 'shield', desc: 'Ed25519 signed offline license keys' },
  { id: 'transactions', name: 'Payments & GST Invoices', icon: 'credit-card', desc: 'Razorpay billing & tax ledgers' },
  { id: 'release', name: 'Windows .exe Release', icon: 'download', desc: 'Desktop installer distribution & SHA256' },
  { id: 'blog', name: 'Blog & Knowledge CMS', icon: 'file-text', desc: 'Public website articles & guides' },
]

function switchTab(tabId: string) {
  router.push({ path: '/admin/platform', query: { tab: tabId } })
}

function isCurrentTab(tabId: string) {
  if (route.path !== '/admin/platform') return false
  const active = (route.query.tab as string) || 'plans'
  return active === tabId
}
</script>

<template>
  <div class="min-h-screen bg-[#f9f8fe] dark:bg-[#0e101c] flex flex-col font-sans text-slate-900 dark:text-slate-100 antialiased selection:bg-[#bee1fb] selection:text-[#1c4372]">
    <!-- Top Platform Vendor Header Bar -->
    <header class="sticky top-0 z-40 bg-white/95 dark:bg-[#15182a]/95 backdrop-blur-md border-b border-[#ede9f7] dark:border-[#23273e] shadow-2xs">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <!-- Brand & Vendor Super Admin Identity -->
        <div class="flex items-center space-x-3">
          <NuxtLink to="/admin/platform" class="flex items-center space-x-2.5 group">
            <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-[#2576d2] to-[#5eaef5] text-white flex items-center justify-center font-black text-sm shadow-xs group-hover:scale-105 transition-transform">
              AH
            </div>
            <div class="flex flex-col">
              <span class="font-black text-base text-slate-900 dark:text-white tracking-tight leading-tight">Aarozi Healthcare</span>
              <span class="text-[10px] font-semibold text-slate-400">Cloud Platform Vendor Console</span>
            </div>
          </NuxtLink>

          <span class="hidden sm:inline text-slate-300 dark:text-slate-700">|</span>

          <span class="hidden sm:inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#f0f7fe] dark:bg-[#1d273d] text-[#1c5fae] dark:text-[#90ccf9] border border-[#bee1fb] dark:border-[#2576d2]/50">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Super Admin (Root Vendor)</span>
          </span>
        </div>

        <!-- Center / Right Actions -->
        <div class="flex items-center space-x-3">
          <!-- View Public Web Application Link -->
          <NuxtLink to="/" target="_blank" class="hidden md:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-300 hover:text-[#2576d2] dark:hover:text-[#90ccf9] hover:bg-[#f0f7fe] dark:hover:bg-[#1d273d] transition-colors border border-transparent hover:border-[#bee1fb] dark:hover:border-[#2576d2]/40">
            <Icon name="external-link" size="xs" />
            <span>View Public Website</span>
          </NuxtLink>

          <!-- Current Admin Pill -->
          <div class="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-[#ede9f7] dark:border-[#23273e] text-xs">
            <Icon name="shield-check" size="xs" class="text-emerald-500" />
            <span class="font-bold text-slate-700 dark:text-slate-200">{{ currentAdmin?.email || 'superadmin@aarozi.in' }}</span>
          </div>

          <!-- Theme Toggle -->
          <button
            type="button"
            class="p-2 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
            :title="isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme'"
            aria-label="Toggle theme"
            @click="toggleTheme"
          >
            <Icon :name="isDark ? 'sun' : 'moon'" size="sm" />
          </button>

          <!-- Logout Button -->
          <Button variant="secondary" size="xs" @click="logout">
            <template #icon-left><Icon name="log-out" size="xs" /></template>
            <span class="font-bold">Sign Out</span>
          </Button>
        </div>
      </div>

      <!-- Dedicated Super Admin Horizontal Navigation (ZERO Clinical Modules) -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-[#ede9f7] dark:border-[#23273e] flex items-center space-x-1 overflow-x-auto py-1.5">
        <button
          v-for="item in adminNavItems"
          :key="item.id"
          type="button"
          :class="[
            'px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-2 shrink-0 select-none',
            isCurrentTab(item.id)
              ? 'bg-[#2576d2] text-white shadow-xs'
              : 'text-slate-600 dark:text-slate-300 hover:bg-[#f0f7fe] dark:hover:bg-[#1d273d] hover:text-[#2576d2] dark:hover:text-[#90ccf9]'
          ]"
          @click="switchTab(item.id)"
        >
          <Icon :name="item.icon" size="xs" />
          <span>{{ item.name }}</span>
        </button>
      </div>
    </header>

    <!-- Super Admin Main Content -->
    <main class="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
      <slot />
    </main>

    <!-- Clean Vendor Admin Footer -->
    <footer class="bg-white/80 dark:bg-[#15182a]/80 border-t border-[#ede9f7] dark:border-[#23273e] px-6 py-4 text-xs text-slate-500 dark:text-slate-400">
      <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="flex items-center space-x-2">
          <span class="font-black text-slate-800 dark:text-slate-200">Aarozi Cloud Platform</span>
          <span>&bull;</span>
          <span>SaaS Vendor Administration &bull; Ed25519 Cryptographic Licensing Hub</span>
        </div>
        <div class="text-[11px] text-slate-400">
          Super Admin Console &bull; Hosted on Vercel &bull; 2026
        </div>
      </div>
    </footer>

    <!-- Global Toast Notifications -->
    <ToastProvider />
  </div>
</template>

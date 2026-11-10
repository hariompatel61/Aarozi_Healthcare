<script setup lang="ts">
import { useCustomerAuth } from '~/composables/useCustomerAuth'
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'
import ToastProvider from '~/components/ui/ToastProvider.vue'

const { profile, logout } = useCustomerAuth()
const route = useRoute()

const navTabs = [
  { name: 'Dashboard Overview', path: '/account', icon: 'cube' },
  { name: 'Software Licences', path: '/account/licences', icon: 'shield' },
  { name: 'Installer Downloads', path: '/account/downloads', icon: 'arrow-down' },
  { name: 'Orders & Invoices', path: '/account/orders', icon: 'document' },
  { name: 'Support & Tickets', path: '/account/support', icon: 'chat' },
]

function isActive(path: string) {
  if (path === '/account') return route.path === '/account'
  return route.path.startsWith(path)
}
</script>

<template>
  <div class="min-h-screen bg-[#f9f8fe] dark:bg-[#0e101c] font-sans text-slate-900 dark:text-slate-100 flex flex-col selection:bg-[#bee1fb] selection:text-[#1c4372]">
    <!-- Top Customer Portal Navigation Bar -->
    <header class="sticky top-0 z-40 bg-white dark:bg-[#15182a] border-b border-[#ede9f7] dark:border-[#23273e] shadow-2xs">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <!-- Brand & Context -->
        <div class="flex items-center space-x-3">
          <NuxtLink to="/" class="flex items-center space-x-2.5 group">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-[#2576d2] to-[#5eaef5] text-white flex items-center justify-center font-black text-sm shadow-xs">
              AH
            </div>
            <span class="font-extrabold text-base text-slate-900 dark:text-white tracking-tight">Aarozi Healthcare</span>
          </NuxtLink>
          <span class="text-slate-300 dark:text-slate-700">/</span>
          <span class="px-2.5 py-0.5 text-xs font-bold bg-[#f0f7fe] text-[#1c5fae] dark:bg-[#1d273d] dark:text-[#90ccf9] rounded-md border border-[#bee1fb] dark:border-[#2576d2]/50">
            Customer Account Portal
          </span>
        </div>

        <!-- Center Registered Laboratory Info -->
        <div class="hidden md:flex items-center space-x-3 bg-slate-50 dark:bg-slate-800/60 px-3.5 py-1.5 rounded-lg border border-[#ede9f7] dark:border-[#23273e] text-xs">
          <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span class="font-bold text-slate-800 dark:text-slate-200">{{ profile.lab_name }}</span>
          <span class="text-slate-400">&bull;</span>
          <span class="text-slate-500 font-mono text-[11px]">{{ profile.email }}</span>
        </div>

        <!-- Right User Actions -->
        <div class="flex items-center space-x-3">
          <NuxtLink to="/pricing">
            <Button variant="secondary" size="xs">
              <template #icon-left><Icon name="shopping-cart" size="xs" /></template>
              Buy Add-ons / Renew
            </Button>
          </NuxtLink>

          <Button variant="ghost" size="xs" @click="logout">
            <template #icon-left><Icon name="logout" size="xs" /></template>
            Sign Out
          </Button>
        </div>
      </div>

      <!-- Secondary Subnav Tabs -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-[#ede9f7] dark:border-[#23273e] flex overflow-x-auto">
        <NuxtLink
          v-for="tab in navTabs"
          :key="tab.path"
          :to="tab.path"
          class="px-4 py-3 text-xs font-bold border-b-2 flex items-center space-x-2 whitespace-nowrap transition-colors"
          :class="[
            isActive(tab.path)
              ? 'border-[#2576d2] text-[#2576d2] dark:text-[#90ccf9]'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          ]"
        >
          <Icon :name="tab.icon" size="xs" />
          <span>{{ tab.name }}</span>
        </NuxtLink>
      </div>
    </header>

    <!-- Main Customer Body -->
    <main class="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
      <slot />
    </main>

    <!-- Clean Customer Footer -->
    <footer class="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 py-6 text-xs text-slate-500 text-center">
      <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div>
          Aarozi Commercial Account Management &bull; Support: <a href="mailto:support@aarozi.in" class="text-teal-600 hover:underline">support@aarozi.in</a> &bull; +91 98200 12345
        </div>
        <div>
          <NuxtLink to="/" class="hover:text-teal-600">Back to Public Website &rarr;</NuxtLink>
        </div>
      </div>
    </footer>

    <ToastProvider />
  </div>
</template>


<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from '~/components/shell/Sidebar.vue'
import TopHeader from '~/components/shell/TopHeader.vue'
import CommandPalette from '~/components/shell/CommandPalette.vue'
import ToastProvider from '~/components/ui/ToastProvider.vue'

const isSidebarCollapsed = ref(false)
const isMobileOpen = ref(false)
const commandPaletteRef = ref<InstanceType<typeof CommandPalette> | null>(null)

function openCommandPalette() {
  commandPaletteRef.value?.open()
}
</script>

<template>
  <div class="min-h-screen bg-[#f9f8fe] dark:bg-[#0e101c] flex font-sans text-slate-900 dark:text-slate-100 antialiased selection:bg-[#bee1fb] selection:text-[#1c4372]">
    <!-- Collapsible Operational Sidebar matching Reference Design -->
    <Sidebar
      v-model:collapsed="isSidebarCollapsed"
      :mobile-open="isMobileOpen"
      @close-mobile="isMobileOpen = false"
    />

    <!-- Main Content Area -->
    <div
      :class="[
        'flex-1 flex flex-col min-w-0 transition-all duration-200',
        isSidebarCollapsed ? 'lg:pl-16' : 'lg:pl-56'
      ]"
    >
      <!-- Top Navigation Header matching Reference -->
      <TopHeader
        :collapsed="isSidebarCollapsed"
        @toggle-mobile="isMobileOpen = !isMobileOpen"
        @open-command-palette="openCommandPalette"
      />

      <!-- Page Body -->
      <main class="flex-1 w-full p-4 sm:p-6 lg:p-6">
        <slot />
      </main>

      <!-- Clean Clinical Footer -->
      <footer class="bg-white/90 dark:bg-[#15182a] border-t border-[#ede9f7] dark:border-[#23273e] px-6 py-2.5 text-xs text-slate-500 dark:text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div class="flex items-center space-x-2">
          <span class="font-semibold text-slate-800 dark:text-slate-200">Aarozi Healthcare</span>
          <span>&bull;</span>
          <span>Laboratory Information System &bull; Pathology &bull; Billing &bull; Blood Bank</span>
        </div>
        <div class="text-[11px] text-slate-400 dark:text-slate-500">
          Complete UI/UX for Modern Indian Pathology Laboratory &bull; 2026
        </div>
      </footer>
    </div>

    <!-- Global Toast Notifications Provider -->
    <ToastProvider />

    <!-- Global Command Palette (Ctrl+K Quick Navigator) -->
    <CommandPalette ref="commandPaletteRef" />
  </div>
</template>
<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { usePlatformStore } from '~/composables/usePlatformStore'
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'
import Badge from '~/components/ui/Badge.vue'

definePageMeta({
  layout: 'customer',
})

const { windowsRelease, initStore } = usePlatformStore()

onMounted(() => {
  initStore()
})

const packages = computed(() => [
  {
    name: 'Aarozi Healthcare Master LIS Installer (.exe)',
    version: windowsRelease.value.version,
    fileSize: windowsRelease.value.fileSize,
    date: windowsRelease.value.releaseDate,
    format: 'Windows Setup .exe',
    url: windowsRelease.value.downloadUrl,
    sha256: windowsRelease.value.sha256,
    recommended: true,
  },
  {
    name: 'Aarozi Portable ZIP Package (No Admin Rights Needed)',
    version: `${windowsRelease.value.version}-Portable`,
    fileSize: '86.2 MB',
    date: windowsRelease.value.releaseDate,
    format: '.zip Archive',
    url: '/downloads/Aarozi-LIS-Portable-v2.4.0.zip',
    sha256: '7c8b9a01f2e3d4c5b6a7890123456789abcdef0123456789abcdef0123456789',
    recommended: false,
  },
  {
    name: 'Master PC Autostart Windows Service Script',
    version: 'v1.0.0',
    fileSize: '15 KB',
    date: '01 Nov 2026',
    format: '.bat PowerShell',
    url: '/downloads/register-aarozi-service.bat',
    sha256: '3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e',
    recommended: false,
  },
])
</script>

<template>
  <div class="space-y-8 text-slate-900 dark:text-slate-100">
    <div>
      <h1 class="text-2xl font-black text-slate-900 dark:text-white">Windows Software Downloads</h1>
      <p class="text-xs text-slate-500">Official verified binaries and server deployment packages for your Laboratory Master PC</p>
    </div>

    <!-- Downloads Grid -->
    <div class="space-y-4">
      <div
        v-for="pkg in packages"
        :key="pkg.name"
        class="rounded-3xl bg-white dark:bg-[#15182a] border p-6 sm:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-6 shadow-2xs"
        :class="pkg.recommended ? 'border-[#2576d2] ring-1 ring-[#2576d2]/20' : 'border-[#ede9f7] dark:border-[#23273e]'"
      >
        <div class="space-y-2 max-w-xl">
          <div class="flex items-center space-x-2">
            <h3 class="text-base font-bold text-slate-900 dark:text-white">{{ pkg.name }}</h3>
            <Badge v-if="pkg.recommended" variant="info" size="sm">
              Recommended
            </Badge>
          </div>

          <div class="flex flex-wrap items-center gap-3 text-xs text-slate-500">
            <span>Version: <strong class="text-slate-700 dark:text-slate-300">{{ pkg.version }}</strong></span>
            <span>&bull;</span>
            <span>Size: <strong class="text-slate-700 dark:text-slate-300">{{ pkg.fileSize }}</strong></span>
            <span>&bull;</span>
            <span>Released: {{ pkg.date }}</span>
          </div>

          <p class="font-mono text-[10px] text-slate-400 break-all select-all">
            SHA-256: {{ pkg.sha256 }}
          </p>
        </div>

        <a :href="pkg.url" download class="shrink-0">
          <Button variant="primary" size="md" class="w-full sm:w-auto font-bold shadow-xs">
            <template #icon-left><Icon name="download" size="xs" /></template>
            <span>Download {{ pkg.format }}</span>
          </Button>
        </a>
      </div>
    </div>
  </div>
</template>

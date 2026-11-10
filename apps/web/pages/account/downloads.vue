<script setup lang="ts">
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'

definePageMeta({
  layout: 'customer',
})

const packages = [
  {
    name: 'Aarozi Healthcare Master Server Installer (x64)',
    version: 'v1.0.4-LTS',
    fileSize: '30.6 MB',
    date: '10 Nov 2026',
    format: 'Setup .exe',
    url: '/downloads/AaroziHealthcareServer-v1.0.4-Setup.exe',
    sha256: 'a9f1b4c83d7e52a09f3e4c6b8d1a2f5e7c9b0a1d3f5e7c9b0a1d3f5e7c9b0a1d',
    recommended: true,
  },
  {
    name: 'Aarozi Portable ZIP Package (No Admin Rights Needed)',
    version: 'v1.0.4-Portable',
    fileSize: '32.1 MB',
    date: '10 Nov 2026',
    format: '.zip Archive',
    url: '/downloads/AaroziHealthcareServer-v1.0.4-Portable.zip',
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
]
</script>

<template>
  <div class="space-y-8">
    <div>
      <h1 class="text-2xl font-black text-slate-900 dark:text-white">Windows Software Downloads</h1>
      <p class="text-xs text-slate-500">Official verified binaries and server deployment scripts for your Master PC</p>
    </div>

    <!-- Downloads Grid -->
    <div class="space-y-4">
      <div
        v-for="pkg in packages"
        :key="pkg.name"
        class="rounded-3xl bg-white dark:bg-slate-900 border p-6 sm:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-6 shadow-sm"
        :class="pkg.recommended ? 'border-teal-500/50 ring-1 ring-teal-500/20' : 'border-slate-200 dark:border-slate-800'"
      >
        <div class="space-y-2 max-w-xl">
          <div class="flex items-center space-x-2">
            <h3 class="text-base font-bold text-slate-900 dark:text-white">{{ pkg.name }}</h3>
            <span
              v-if="pkg.recommended"
              class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-teal-100 text-teal-800 dark:bg-teal-950 dark:text-teal-300"
            >
              Recommended
            </span>
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
          <Button variant="primary" size="sm" class="w-full sm:w-auto font-bold">
            <template #icon-left><Icon name="download" size="xs" /></template>
            Download ({{ pkg.format }})
          </Button>
        </a>
      </div>
    </div>
  </div>
</template>

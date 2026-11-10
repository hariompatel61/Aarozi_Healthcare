<script setup lang="ts">
import { ref } from 'vue'
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const releaseInfo = {
  version: 'v1.0.4-LTS',
  releaseDate: '10 November 2026',
  fileSize: '30.6 MB',
  targetOS: 'Windows 10 / 11 (64-bit)',
  sha256: 'a9f1b4c83d7e52a09f3e4c6b8d1a2f5e7c9b0a1d3f5e7c9b0a1d3f5e7c9b0a1d',
  downloadUrl: '/downloads/AaroziHealthcareServer-v1.0.4-Setup.exe',
}

const copied = ref(false)
const copySha = () => {
  navigator.clipboard?.writeText(releaseInfo.sha256)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="download" size="xs" />
        <span>Official Windows Release Center</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Download Aarozi LIS for Windows
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Install the complete offline-first laboratory information system on your Master PC. Works independently on your local LAN with zero mandatory cloud dependencies.
      </p>
    </div>

    <!-- Release Download Card -->
    <div class="max-w-3xl mx-auto rounded-3xl border border-teal-200 dark:border-teal-900/60 bg-gradient-to-b from-teal-50/50 to-white dark:from-teal-950/20 dark:to-slate-900 p-8 sm:p-12 shadow-xl space-y-8">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-6 border-b pb-6 border-slate-200 dark:border-slate-800">
        <div class="space-y-1 text-center sm:text-left">
          <div class="flex items-center space-x-2 justify-center sm:justify-start">
            <h3 class="text-2xl font-black text-slate-900 dark:text-white">Aarozi Healthcare Master Server</h3>
            <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-300">
              {{ releaseInfo.version }}
            </span>
          </div>
          <p class="text-xs text-slate-500">Standalone offline server & UI runtime for lab workstations</p>
        </div>

        <a :href="releaseInfo.downloadUrl" download class="w-full sm:w-auto">
          <Button variant="primary" size="lg" class="w-full sm:w-auto justify-center font-bold px-8 shadow-lg shadow-teal-500/20">
            <Icon name="download" size="sm" class="mr-2" />
            <span>Download Installer (.exe)</span>
          </Button>
        </a>
      </div>

      <!-- Specs & SHA -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
        <div><span class="text-slate-400 block">File Size</span><strong class="text-slate-900 dark:text-white">{{ releaseInfo.fileSize }}</strong></div>
        <div><span class="text-slate-400 block">Release Date</span><strong class="text-slate-900 dark:text-white">{{ releaseInfo.releaseDate }}</strong></div>
        <div><span class="text-slate-400 block">Compatibility</span><strong class="text-slate-900 dark:text-white">{{ releaseInfo.targetOS }}</strong></div>
        <div><span class="text-slate-400 block">Licence</span><strong class="text-teal-600 dark:text-teal-400">14-Day Free Trial</strong></div>
      </div>

      <!-- Cryptographic Checksum -->
      <div class="p-4 rounded-2xl bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2">
        <div class="flex items-center justify-between text-[11px] text-slate-500">
          <span>SHA-256 Checksum (Integrity Verification)</span>
          <button @click="copySha" class="text-teal-600 dark:text-teal-400 font-bold hover:underline">
            {{ copied ? 'Copied ✓' : 'Copy Hash' }}
          </button>
        </div>
        <p class="font-mono text-[10px] break-all text-slate-700 dark:text-slate-300 select-all">
          {{ releaseInfo.sha256 }}
        </p>
      </div>
    </div>

    <!-- 3-Step Setup Instructions -->
    <div class="max-w-4xl mx-auto space-y-8">
      <h2 class="text-2xl font-bold text-center text-slate-900 dark:text-white">
        Quick 3-Minute Master PC Setup
      </h2>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm">
          <div class="w-8 h-8 rounded-full bg-teal-600 text-white font-bold flex items-center justify-center text-xs">1</div>
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">Run Installer on Master PC</h3>
          <p class="text-xs text-slate-500 leading-relaxed">
            Double-click the downloaded setup file. Follow the wizard prompts to install the embedded database and web runtime.
          </p>
        </div>

        <div class="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm">
          <div class="w-8 h-8 rounded-full bg-teal-600 text-white font-bold flex items-center justify-center text-xs">2</div>
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">Launch & Copy Machine ID</h3>
          <p class="text-xs text-slate-500 leading-relaxed">
            Open Aarozi from the desktop shortcut. Go to Settings > Licensing and copy your unique hardware Machine ID.
          </p>
        </div>

        <div class="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm">
          <div class="w-8 h-8 rounded-full bg-teal-600 text-white font-bold flex items-center justify-center text-xs">3</div>
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">Activate & Connect Workstations</h3>
          <p class="text-xs text-slate-500 leading-relaxed">
            Download your .lic file from your Aarozi Account portal, load it into the software, and open the system on your LAN desks.
          </p>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

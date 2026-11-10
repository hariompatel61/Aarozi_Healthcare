<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePlatformStore } from '~/composables/usePlatformStore'
import Button from '~/components/ui/Button.vue'
import Badge from '~/components/ui/Badge.vue'
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const { windowsRelease, initStore } = usePlatformStore()

onMounted(() => {
  initStore()
})

const copied = ref(false)
const copySha = () => {
  navigator.clipboard?.writeText(windowsRelease.value.sha256)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16 text-slate-900 dark:text-slate-100">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#f0f7fe] dark:bg-[#1d273d] text-[#1c5fae] dark:text-[#90ccf9] border border-[#bee1fb] dark:border-[#2576d2]/50">
        <Icon name="download" size="xs" />
        <span>Official Windows Release Center</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Download Aarozi LIS for Windows
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-300">
        Install the complete offline-first laboratory information system on your Master PC. Works independently on your local LAN with zero mandatory cloud dependencies.
      </p>
    </div>

    <!-- Release Download Card -->
    <div class="max-w-3xl mx-auto rounded-3xl border border-[#ede9f7] dark:border-[#23273e] bg-white dark:bg-[#15182a] p-8 sm:p-12 shadow-md space-y-8">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-6 border-b pb-6 border-[#ede9f7] dark:border-[#23273e]">
        <div class="space-y-1 text-center sm:text-left">
          <div class="flex items-center space-x-2 justify-center sm:justify-start">
            <h3 class="text-2xl font-black text-slate-900 dark:text-white">Aarozi Healthcare Master LIS</h3>
            <Badge variant="info" size="sm">
              {{ windowsRelease.version }}
            </Badge>
          </div>
          <p class="text-xs text-slate-500">Standalone offline server &amp; clinical UI runtime for lab workstations</p>
        </div>

        <a :href="windowsRelease.downloadUrl" download class="w-full sm:w-auto">
          <Button variant="primary" size="lg" class="w-full sm:w-auto justify-center font-bold px-8 shadow-lg shadow-[#2576d2]/20">
            <template #icon-left><Icon name="download" size="sm" /></template>
            <span>Download Installer (.exe)</span>
          </Button>
        </a>
      </div>

      <!-- Specs & SHA -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
        <div><span class="text-slate-400 block">File Size</span><strong class="text-slate-900 dark:text-white">{{ windowsRelease.fileSize }}</strong></div>
        <div><span class="text-slate-400 block">Release Date</span><strong class="text-slate-900 dark:text-white">{{ windowsRelease.releaseDate }}</strong></div>
        <div><span class="text-slate-400 block">Compatibility</span><strong class="text-slate-900 dark:text-white">{{ windowsRelease.targetOS }}</strong></div>
        <div><span class="text-slate-400 block">Licence</span><strong class="text-[#2576d2] dark:text-[#90ccf9]">14-Day Free Trial / Paid</strong></div>
      </div>

      <!-- Cryptographic Checksum -->
      <div class="p-4 rounded-2xl bg-slate-50 dark:bg-slate-900/60 border border-[#ede9f7] dark:border-[#23273e] space-y-2">
        <div class="flex items-center justify-between text-[11px] text-slate-500">
          <span>SHA-256 Checksum (Integrity Verification)</span>
          <button @click="copySha" class="text-[#2576d2] dark:text-[#90ccf9] font-bold hover:underline cursor-pointer">
            {{ copied ? 'Copied ✓' : 'Copy Hash' }}
          </button>
        </div>
        <p class="font-mono text-[10px] break-all text-slate-700 dark:text-slate-300 select-all">
          {{ windowsRelease.sha256 }}
        </p>
      </div>

      <!-- Customer Portal Login Link -->
      <div class="p-4 rounded-2xl bg-[#f0f7fe] dark:bg-[#1d273d] border border-[#bee1fb] dark:border-[#2576d2]/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div class="text-slate-700 dark:text-slate-300">
          <span class="font-bold">Already purchased a licence?</span>
          <span class="block sm:inline sm:ml-1 text-slate-500">Sign in to your customer portal to download your activation license file.</span>
        </div>
        <NuxtLink to="/login" class="shrink-0">
          <Button variant="secondary" size="xs">
            <span>Customer Login (/account)</span>
          </Button>
        </NuxtLink>
      </div>
    </div>

    <!-- 3-Step Setup Instructions -->
    <div class="max-w-4xl mx-auto space-y-8">
      <h2 class="text-2xl font-bold text-center text-slate-900 dark:text-white">
        Quick 3-Minute Master PC Setup
      </h2>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="p-6 rounded-3xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] space-y-3 shadow-2xs">
          <div class="w-8 h-8 rounded-full bg-[#2576d2] text-white font-bold flex items-center justify-center text-xs">1</div>
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">Run Installer on Master PC</h3>
          <p class="text-xs text-slate-500 leading-relaxed">
            Double-click the downloaded setup file. Follow the wizard prompts to install the embedded database and local LAN server runtime.
          </p>
        </div>

        <div class="p-6 rounded-3xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] space-y-3 shadow-2xs">
          <div class="w-8 h-8 rounded-full bg-[#2576d2] text-white font-bold flex items-center justify-center text-xs">2</div>
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">Activate With Your License</h3>
          <p class="text-xs text-slate-500 leading-relaxed">
            Log in to <NuxtLink to="/account" class="text-[#2576d2] hover:underline font-bold">your account</NuxtLink> to download your signed <code class="font-mono text-[#2576d2]">aarozi.license</code> file or paste your license key ID.
          </p>
        </div>

        <div class="p-6 rounded-3xl bg-white dark:bg-[#15182a] border border-[#ede9f7] dark:border-[#23273e] space-y-3 shadow-2xs">
          <div class="w-8 h-8 rounded-full bg-[#2576d2] text-white font-bold flex items-center justify-center text-xs">3</div>
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">Connect LAN Workstations</h3>
          <p class="text-xs text-slate-500 leading-relaxed">
            Other PCs in your lab (Reception, Phlebotomy, Pathologist Desk) can access the system via browser or LAN client with zero internet needed.
          </p>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

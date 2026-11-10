<script setup lang="ts">
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
    <!-- Header -->
    <div class="text-center space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="key" size="xs" />
        <span>Activation Guide</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        How to Activate Aarozi LIS on Your Master PC
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Activate your laboratory software in 3 simple steps without needing continuous internet connectivity.
      </p>
    </div>

    <!-- 3 Step Detailed Walkthrough -->
    <div class="space-y-6">
      <!-- Step 1 -->
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-2xl bg-teal-600 text-white font-bold flex items-center justify-center text-sm">
            1
          </div>
          <div>
            <h3 class="text-base font-bold text-slate-900 dark:text-white">Retrieve Your Master PC Hardware Machine ID</h3>
            <p class="text-xs text-slate-500">Every computer has a unique hardware cryptographic identifier</p>
          </div>
        </div>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed pl-13">
          Open the installed Aarozi Healthcare desktop software on your Master PC. Navigate to <strong>Settings > System & Licensing</strong>. You will see a Machine ID formatted like: <code class="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-teal-600 font-mono font-bold">HW-89F4-A012-78BC</code>. Click the <strong>Copy Machine ID</strong> button.
        </p>
      </div>

      <!-- Step 2 -->
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-2xl bg-teal-600 text-white font-bold flex items-center justify-center text-sm">
            2
          </div>
          <div>
            <h3 class="text-base font-bold text-slate-900 dark:text-white">Download Your Signed Licence File (.lic)</h3>
            <p class="text-xs text-slate-500">From the Aarozi Customer Account portal</p>
          </div>
        </div>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed pl-13">
          Sign into your <NuxtLink to="/account" class="text-teal-600 font-bold hover:underline">Customer Account</NuxtLink>. Under <strong>Software Licences</strong>, paste your Machine ID if prompted, and click <strong>Download .lic File</strong>. Save this file to a USB thumb drive or your Downloads folder.
        </p>
      </div>

      <!-- Step 3 -->
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-2xl bg-teal-600 text-white font-bold flex items-center justify-center text-sm">
            3
          </div>
          <div>
            <h3 class="text-base font-bold text-slate-900 dark:text-white">Import the Licence into Aarozi Desktop</h3>
            <p class="text-xs text-slate-500">Instantly unlocks full clinical and billing capabilities</p>
          </div>
        </div>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed pl-13">
          Return to the Aarozi software on your Master PC. Click <strong>Upload Licence File</strong>, select the downloaded <code class="text-teal-600 font-mono">.lic</code> file, and click <strong>Apply Licence</strong>. The software instantly verifies the Ed25519 signature and unlocks unrestricted operation!
        </p>
      </div>
    </div>

    <!-- Troubleshooting Help -->
    <div class="p-6 rounded-3xl bg-slate-900 text-white border border-slate-800 flex items-center justify-between">
      <div class="space-y-1">
        <h4 class="text-sm font-bold text-teal-400">Need personal assistance?</h4>
        <p class="text-xs text-slate-400">Our engineering team can connect remotely via AnyDesk to activate for you.</p>
      </div>
      <NuxtLink to="/contact">
        <Button variant="primary" size="sm">Get Remote Help</Button>
      </NuxtLink>
    </div>

    <CtaBanner />
  </div>
</template>

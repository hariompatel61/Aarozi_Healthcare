<script setup lang="ts">
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <NuxtLink to="/features" class="inline-flex items-center space-x-1.5 text-xs font-bold text-teal-600 hover:underline">
        <Icon name="arrow-left" size="xs" />
        <span>All Features</span>
      </NuxtLink>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        1-Click Automated Backup & Disaster Recovery
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Safeguard 100% of your clinical, patient, and billing records locally with encrypted scheduled snapshots to external drives, USB, or local NAS.
      </p>
    </div>

    <!-- Core Capabilities Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="clock" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Scheduled Daily Snapshots</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Configure automatic night backups at your preferred time. The system creates compressed SQLite transaction archives without interrupting lab operations.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
          <Icon name="shield" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">AES-256 Checksum Encryption</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Every snapshot includes cryptographic SHA-256 integrity verification and AES encryption, ensuring your patient data remains safe from unauthorized tampering or ransomware.
        </p>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="refresh" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Zero-Loss 1-Click Restore</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          In the event of hardware failure, install Aarozi on a replacement PC, select your latest backup file, and restore your full lab in under 60 seconds.
        </p>
      </div>
    </div>

    <!-- Workflow Detail Card -->
    <div class="p-8 sm:p-12 rounded-3xl bg-slate-900 text-white border border-slate-800 space-y-6">
      <div class="max-w-3xl space-y-3">
        <h2 class="text-2xl font-bold tracking-tight">Your Patient Data Stays In Your Hands — Never Leaked to Third Parties</h2>
        <p class="text-xs sm:text-sm text-slate-400 leading-relaxed">
          Cloud-based LIS platforms lock your laboratory into endless recurring fees and store sensitive diagnostic reports on multi-tenant servers. Aarozi guarantees complete data sovereignty: your data lives on your PC, backed up to your physical drives.
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs pt-4 border-t border-slate-800">
        <div><strong class="text-teal-400 block mb-1">External USB Mirroring</strong><span>Auto-detects connected external drives and creates duplicate mirrors automatically.</span></div>
        <div><strong class="text-teal-400 block mb-1">Local NAS & Shared Drive</strong><span>Supports UNC network paths (\\NAS\Backups) for laboratory IT infrastructure.</span></div>
        <div><strong class="text-teal-400 block mb-1">Atomic Point-in-Time</strong><span>Zero database locking or query pausing during snapshot generation.</span></div>
        <div><strong class="text-teal-400 block mb-1">Audit Trail History</strong><span>Complete log of every backup creation, file size, checksum, and restore event.</span></div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

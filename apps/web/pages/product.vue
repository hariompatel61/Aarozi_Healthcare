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
    <!-- Header Hero -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300 border border-teal-200">
        Product Architecture
      </span>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Engineered for Complete Diagnostic Autonomy
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400 leading-relaxed">
        Aarozi Healthcare is architected as an offline-first desktop server application that runs directly on your laboratory's master computer and coordinates with all local LAN workstations.
      </p>
    </div>

    <!-- 3-Pillar Architectural Breakdown -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-lg space-y-4">
        <div class="w-12 h-12 rounded-2xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold text-xl">
          01
        </div>
        <h3 class="text-lg font-bold text-slate-900 dark:text-white">Local Master PC Server</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          The core FastAPI backend, transactional database engine (SQLite/PostgreSQL), and report compiler run natively on your Windows master workstation. All clinical transactions commit directly to disk in milliseconds.
        </p>
        <ul class="text-xs text-slate-500 space-y-1.5 pt-2">
          <li>&bull; Zero dependency on cloud availability</li>
          <li>&bull; Real-time serial port analyzer polling</li>
          <li>&bull; Local PDF compilation under 200ms</li>
        </ul>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-lg space-y-4">
        <div class="w-12 h-12 rounded-2xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold text-xl">
          02
        </div>
        <h3 class="text-lg font-bold text-slate-900 dark:text-white">Local Area Network (LAN) Hub</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Using standard clinic Wi-Fi or Ethernet switches, secondary workstations (front-desk cashier, phlebotomy chair, laboratory bench, and pathologist office) access the master system through their local browser.
        </p>
        <ul class="text-xs text-slate-500 space-y-1.5 pt-2">
          <li>&bull; Supports 15 to 50 concurrent workstations</li>
          <li>&bull; Sub-10ms network latency inside the clinic</li>
          <li>&bull; Role-based station profiles (POS, Tech, Doctor)</li>
        </ul>
      </div>

      <div class="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-lg space-y-4">
        <div class="w-12 h-12 rounded-2xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-xl">
          03
        </div>
        <h3 class="text-lg font-bold text-slate-900 dark:text-white">Cryptographic Offline Licensing</h3>
        <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Licences are signed on our central portal using root Ed25519 asymmetric cryptography. When loaded into your local software, the signature verifies offline using the embedded public key without phone-home requirements.
        </p>
        <ul class="text-xs text-slate-500 space-y-1.5 pt-2">
          <li>&bull; Tamper-proof license structure</li>
          <li>&bull; Re-install and offline recovery safe</li>
          <li>&bull; Safe clock-rollback protection</li>
        </ul>
      </div>
    </div>

    <!-- Deep-Dive Specifications -->
    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 sm:p-12 shadow-lg space-y-8">
      <h2 class="text-2xl font-bold text-slate-900 dark:text-white">
        Detailed System Architecture & Specifications
      </h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-8 text-xs">
        <div class="space-y-3">
          <h4 class="font-bold text-sm text-teal-600 dark:text-teal-400 uppercase tracking-wider">Clinical Data Boundaries</h4>
          <p class="text-slate-600 dark:text-slate-400 leading-relaxed">
            Patient demographic details, Aadhaar/phone numbers, diagnostic parameters, numerical results, and doctor signatures remain strictly inside your clinic's storage. Aarozi never uploads patient health information to public servers.
          </p>
        </div>

        <div class="space-y-3">
          <h4 class="font-bold text-sm text-teal-600 dark:text-teal-400 uppercase tracking-wider">Analyzer Interfacing</h4>
          <p class="text-slate-600 dark:text-slate-400 leading-relaxed">
            Built-in ASTM 1394 and HL7 protocol drivers interface seamlessly with automated 3-part & 5-part hematology counters, dry/wet clinical biochemistry analyzers, and urine chemistry strips.
          </p>
        </div>

        <div class="space-y-3">
          <h4 class="font-bold text-sm text-teal-600 dark:text-teal-400 uppercase tracking-wider">Hardware Requirements</h4>
          <p class="text-slate-600 dark:text-slate-400 leading-relaxed">
            Master PC: Windows 10/11 (64-bit), 8 GB RAM, Intel Core i3 or higher, 256 GB SSD. Secondary workstations only require any device with a standard web browser (Chrome, Edge, Firefox).
          </p>
        </div>

        <div class="space-y-3">
          <h4 class="font-bold text-sm text-teal-600 dark:text-teal-400 uppercase tracking-wider">Disaster Recovery & Redundancy</h4>
          <p class="text-slate-600 dark:text-slate-400 leading-relaxed">
            Automated hourly snapshot backups save encrypted archive files directly to secondary hard drives, network attached storage (NAS), or external USB storage with single-click restore capabilities.
          </p>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

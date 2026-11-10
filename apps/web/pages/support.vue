<script setup lang="ts">
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const guides = [
  {
    title: 'Master PC Installation & Initial Configuration',
    category: 'Getting Started',
    desc: 'Step-by-step walkthrough to install the Aarozi server binary, initialize the local clinical database, and create your lab administrator login.',
  },
  {
    title: 'LAN Hub Workstation Connectivity Guide',
    category: 'Networking',
    desc: 'Configuring Windows Defender Firewall, finding your Master PC static IP address, and connecting client computers via Chrome or Edge.',
  },
  {
    title: 'Thermal Barcode & Slip Printer Setup',
    category: 'Hardware',
    desc: 'Setting up Zebra, TSC, TVS, and Citizen thermal barcode printers for standard 50x25mm split-tube labels and 80mm cashier slips.',
  },
  {
    title: 'Licence File (.lic) Activation & Hardware Re-Keying',
    category: 'Licensing',
    desc: 'How to import cryptographically signed Ed25519 license files and transfer your license to a replacement computer.',
  },
  {
    title: 'Daily Automated Database Backups',
    category: 'Data Protection',
    desc: 'Configuring automated scheduled snapshots to external USB hard drives or network NAS storage for zero-loss disaster recovery.',
  },
  {
    title: 'Configuring Custom Reference Ranges & Department Units',
    category: 'Clinical Lab',
    desc: 'Customizing multi-tier biological reference intervals, panic flags, and derived ratio formulas in the test catalog.',
  },
]
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="help-circle" size="xs" />
        <span>Technical Documentation & Help Center</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Aarozi Support & Documentation
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Guides, tutorials, networking instructions, and hardware configuration resources to help your laboratory run smoothly.
      </p>
    </div>

    <!-- Quick Help Channels -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm">
        <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
          <Icon name="phone" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Emergency Phone Helpline</h3>
        <p class="text-xs text-slate-500 leading-relaxed">Direct engineer support for active labs experiencing critical hardware or LAN disruption.</p>
        <a href="tel:+919876543210" class="text-xs font-bold text-teal-600 hover:underline block">+91 98765 43210</a>
      </div>

      <div class="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm">
        <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
          <Icon name="mail" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Email Ticket Desk</h3>
        <p class="text-xs text-slate-500 leading-relaxed">Submit questions about report formats, price lists, or Excel data migration.</p>
        <a href="mailto:support@aarozi.in" class="text-xs font-bold text-sky-600 hover:underline block">support@aarozi.in</a>
      </div>

      <div class="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm">
        <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
          <Icon name="video" size="sm" />
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Remote Desktop Assistance</h3>
        <p class="text-xs text-slate-500 leading-relaxed">Our technicians connect via AnyDesk or TeamViewer to configure printers or LAN workstations for you.</p>
        <span class="text-xs font-bold text-emerald-600 block">Available Daily</span>
      </div>
    </div>

    <!-- Guides Directory -->
    <div class="space-y-6">
      <h2 class="text-2xl font-bold text-slate-900 dark:text-white">Popular Technical Guides</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div
          v-for="g in guides"
          :key="g.title"
          class="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2 hover:border-teal-500 transition-all cursor-pointer shadow-sm"
        >
          <span class="text-[10px] font-bold text-teal-600 uppercase tracking-wider">{{ g.category }}</span>
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">{{ g.title }}</h3>
          <p class="text-xs text-slate-500 leading-relaxed">{{ g.desc }}</p>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

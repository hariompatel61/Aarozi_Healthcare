<script setup lang="ts">
import { ref } from 'vue'
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const activeCategory = ref('all')
const searchQuery = ref('')

const faqs = [
  {
    category: 'architecture',
    q: 'Does Aarozi require continuous internet connectivity to function?',
    a: 'No. Aarozi is built with a strict local-first architecture. The software runs entirely on your laboratory’s Master PC. Registration, test billing, barcoding, analyzer result entry, pathologist approval, and print reporting continue completely uninterrupted even if your broadband cable is cut or disconnected for weeks.',
  },
  {
    category: 'architecture',
    q: 'How do multiple staff members in my lab use the software simultaneously?',
    a: 'Your Master PC functions as a high-speed local LAN Hub. Other computers at reception, phlebotomy, analyzer benches, and doctor reporting rooms simply open their regular web browser (Chrome, Edge) and navigate to the Master PC’s local IP address (e.g. http://192.168.1.100:8000). Up to 50 workstations can operate concurrently over Wi-Fi or Ethernet with sub-10ms response times.',
  },
  {
    category: 'data_security',
    q: 'Where are our patient records, financial invoices, and medical reports stored?',
    a: '100% locally on your Master PC. They are never stored in third-party multi-tenant clouds or scraped by outside entities. You have absolute ownership and physical custody of your patient data and diagnostic history.',
  },
  {
    category: 'data_security',
    q: 'How does backup and disaster recovery work if the Master PC hard drive fails?',
    a: 'Aarozi includes 1-click automated database backups. You can configure it to automatically create encrypted, timestamped snapshots to an external USB drive, a secondary hard drive, or a local network NAS. In case of hardware disaster, install Aarozi on a replacement PC, select your latest backup file, and your lab is 100% restored in under 60 seconds.',
  },
  {
    category: 'licensing',
    q: 'What is the difference between Yearly Pro and Lifetime Enterprise?',
    a: 'Yearly Pro (₹14,999/yr) provides 12 months of full software operation, software updates, and standard customer support. Lifetime Enterprise (₹39,999 one-time) grants a permanent, perpetual software license that never expires, unlimited hardware migrations, and lifetime updates.',
  },
  {
    category: 'licensing',
    q: 'What happens when my Yearly Pro license expires? Is my data locked?',
    a: 'Never. In accordance with our non-negotiable software principles, license expiry never deletes or corrupts clinical or financial data. Your laboratory retains full read-only and export access to all historical patient records, test results, and invoices. Entering a new renewal license immediately re-enables active test ordering.',
  },
  {
    category: 'licensing',
    q: 'Can I transfer my license to a new PC if I upgrade my computer?',
    a: 'Yes. Our customer portal includes an automated hardware re-keying tool. If you replace your computer, submit your new Machine ID and download an updated cryptographically signed .lic file for your new hardware.',
  },
  {
    category: 'clinical',
    q: 'Does Aarozi support age- and gender-specific reference ranges and panic alerts?',
    a: 'Yes. The test catalog includes multi-tier biological reference intervals tailored for newborns, pediatric, adult male, adult female, and geriatric patients. High, low, and critical panic values are highlighted in bold red with instant visual flags.',
  },
  {
    category: 'clinical',
    q: 'How do doctor signatures and report QR verification work?',
    a: 'Consultant pathologists and radiodiagnostic doctors can upload their high-resolution digital signatures, which are rendered on final verified reports. Each report includes an Ed25519 tamper-evident QR code that anyone can scan with a smartphone camera to verify authenticity without needing a cloud account.',
  },
  {
    category: 'billing',
    q: 'Can we manage referring doctor commission cuts and diagnostic checkup packages?',
    a: 'Yes. Aarozi features a complete doctor referral ledger with custom percentage or flat incentive structures, payment settlement logs, and instant calculation. You can also group multiple blood, urine, and imaging tests into discounted health checkup packages.',
  },
  {
    category: 'installation',
    q: 'What are the minimum hardware requirements for the Master PC?',
    a: 'Any standard desktop or laptop running Windows 10 or Windows 11 (64-bit), with an Intel Core i3 (or AMD equivalent), 4 GB of RAM (8 GB recommended for 5+ LAN workstations), and 10 GB of free hard drive space. No dedicated server operating system is required.',
  },
]
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="help-circle" size="xs" />
        <span>Answers to Common Inquiries</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Frequently Asked Questions
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Everything you need to know about Aarozi Healthcare’s local-first architecture, hardware requirements, pricing, and clinical workflows.
      </p>
    </div>

    <!-- FAQ Accordion / Grid -->
    <div class="max-w-4xl mx-auto space-y-6">
      <div
        v-for="(faq, index) in faqs"
        :key="index"
        class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 sm:p-8 space-y-3 shadow-sm hover:border-teal-500/50 transition-all"
      >
        <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-start space-x-3">
          <span class="text-teal-600 dark:text-teal-400 font-mono font-bold">Q{{ index + 1 }}.</span>
          <span>{{ faq.q }}</span>
        </h3>
        <p class="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed pl-8">
          {{ faq.a }}
        </p>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>


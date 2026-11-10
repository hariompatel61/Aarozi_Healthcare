<script setup lang="ts">
import Icon from '~/components/ui/Icon.vue'
</script>

<template>
  <footer class="bg-slate-950 text-slate-400 border-t border-slate-800 text-xs">
    <!-- Top Value Props Strip -->
    <div class="border-b border-slate-800/80 bg-slate-900/60 py-6">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-2 md:grid-cols-4 gap-6 text-center md:text-left">
        <div class="flex items-center space-x-3 justify-center md:justify-start">
          <div class="w-8 h-8 rounded-lg bg-teal-500/10 text-teal-400 flex items-center justify-center shrink-0">
            <Icon name="shield" size="sm" />
          </div>
          <div>
            <div class="font-bold text-white text-xs">100% Offline-First</div>
            <div class="text-[11px] text-slate-500">Zero internet required for tests & billing</div>
          </div>
        </div>

        <div class="flex items-center space-x-3 justify-center md:justify-start">
          <div class="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center shrink-0">
            <Icon name="check-circle" size="sm" />
          </div>
          <div>
            <div class="font-bold text-white text-xs">Complete Local Data Ownership</div>
            <div class="text-[11px] text-slate-500">Patient records stay on your master PC</div>
          </div>
        </div>

        <div class="flex items-center space-x-3 justify-center md:justify-start">
          <div class="w-8 h-8 rounded-lg bg-sky-500/10 text-sky-400 flex items-center justify-center shrink-0">
            <Icon name="lock" size="sm" />
          </div>
          <div>
            <div class="font-bold text-white text-xs">Ed25519 Cryptographic Licences</div>
            <div class="text-[11px] text-slate-500">Offline tamper-proof signature verification</div>
          </div>
        </div>

        <div class="flex items-center space-x-3 justify-center md:justify-start">
          <div class="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center shrink-0">
            <Icon name="users" size="sm" />
          </div>
          <div>
            <div class="font-bold text-white text-xs">Multi-PC LAN Workstations</div>
            <div class="text-[11px] text-slate-500">Unlimited reception, lab tech & approval desks</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main 5-Column Navigation Grid -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 grid grid-cols-2 md:grid-cols-5 gap-8 text-left">
      <!-- Col 1: Brand & Mission -->
      <div class="col-span-2 md:col-span-1 space-y-4">
        <div class="flex items-center space-x-2.5">
          <div class="w-8 h-8 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold text-sm">
            AH
          </div>
          <span class="font-extrabold text-base text-white tracking-tight">Aarozi Healthcare</span>
        </div>
        <p class="text-xs text-slate-400 leading-relaxed">
          The unified, offline-first Laboratory Information System (LIS) engineered for modern Indian pathology laboratories, diagnostic centres, and blood banks.
        </p>
        <div class="pt-2 text-[11px] text-slate-500 space-y-1">
          <div><strong class="text-slate-400">Master Windows Installer:</strong> v1.0.4-LTS</div>
          <div><strong class="text-slate-400">Architecture:</strong> Local LAN + Master PC</div>
          <div><strong class="text-slate-400">Compliance:</strong> ISO 15189:2022 & NABL Ready</div>
        </div>
      </div>

      <!-- Col 2: Features -->
      <div class="space-y-3">
        <h4 class="text-xs font-bold uppercase tracking-wider text-white">Features</h4>
        <ul class="space-y-2 text-xs">
          <li><NuxtLink to="/features/patient-management" class="hover:text-teal-400 transition-colors">Patient Management & UHID</NuxtLink></li>
          <li><NuxtLink to="/features/lab-reporting" class="hover:text-teal-400 transition-colors">Laboratory Reporting</NuxtLink></li>
          <li><NuxtLink to="/features/radiology-reporting" class="hover:text-teal-400 transition-colors">Radiology & Ultrasound</NuxtLink></li>
          <li><NuxtLink to="/features/billing" class="hover:text-teal-400 transition-colors">Cashier Billing & GST</NuxtLink></li>
          <li><NuxtLink to="/features/barcode-management" class="hover:text-teal-400 transition-colors">Barcode & Sample Tracking</NuxtLink></li>
          <li><NuxtLink to="/features/qr-reports" class="hover:text-teal-400 transition-colors">QR-Coded Reports</NuxtLink></li>
          <li><NuxtLink to="/features/inventory" class="hover:text-teal-400 transition-colors">Reagents & Inventory</NuxtLink></li>
          <li><NuxtLink to="/features/offline-lan" class="hover:text-teal-400 transition-colors">Offline LAN Operations</NuxtLink></li>
        </ul>
      </div>

      <!-- Col 3: Solutions & Formats -->
      <div class="space-y-3">
        <h4 class="text-xs font-bold uppercase tracking-wider text-white">Solutions & Reports</h4>
        <ul class="space-y-2 text-xs">
          <li><NuxtLink to="/solutions/pathology-lab" class="hover:text-teal-400 transition-colors">Pathology Laboratories</NuxtLink></li>
          <li><NuxtLink to="/solutions/diagnostic-centre" class="hover:text-teal-400 transition-colors">Integrated Diagnostic Centres</NuxtLink></li>
          <li><NuxtLink to="/solutions/radiology-centre" class="hover:text-teal-400 transition-colors">Radiology & Imaging</NuxtLink></li>
          <li><NuxtLink to="/solutions/blood-bank" class="hover:text-teal-400 transition-colors">Blood Banks & Transfusion</NuxtLink></li>
          <li><NuxtLink to="/report-formats" class="hover:text-teal-400 transition-colors">Report Format Library</NuxtLink></li>
          <li><NuxtLink to="/features/data-migration" class="hover:text-teal-400 transition-colors">Software Migration</NuxtLink></li>
          <li><NuxtLink to="/features/backup-restore" class="hover:text-teal-400 transition-colors">Automated Backups</NuxtLink></li>
        </ul>
      </div>

      <!-- Col 4: Resources & Downloads -->
      <div class="space-y-3">
        <h4 class="text-xs font-bold uppercase tracking-wider text-white">Resources & Downloads</h4>
        <ul class="space-y-2 text-xs">
          <li><NuxtLink to="/download" class="hover:text-teal-400 transition-colors font-semibold text-teal-400">Windows Installer (x64)</NuxtLink></li>
          <li><NuxtLink to="/pricing" class="hover:text-teal-400 transition-colors">Transparent Pricing</NuxtLink></li>
          <li><NuxtLink to="/licence/activate" class="hover:text-teal-400 transition-colors">Licence Activation Guide</NuxtLink></li>
          <li><NuxtLink to="/licence/renew" class="hover:text-teal-400 transition-colors">Licence Renewal</NuxtLink></li>
          <li><NuxtLink to="/faq" class="hover:text-teal-400 transition-colors">Frequently Asked Questions</NuxtLink></li>
          <li><NuxtLink to="/blog" class="hover:text-teal-400 transition-colors">Lab Management Blog</NuxtLink></li>
          <li><NuxtLink to="/support" class="hover:text-teal-400 transition-colors">Help Center & Docs</NuxtLink></li>
        </ul>
      </div>

      <!-- Col 5: Customer Portal & Contact -->
      <div class="space-y-3">
        <h4 class="text-xs font-bold uppercase tracking-wider text-white">Customer Portal</h4>
        <ul class="space-y-2 text-xs">
          <li><NuxtLink to="/login" class="hover:text-teal-400 transition-colors">Customer & Staff Login</NuxtLink></li>
          <li><NuxtLink to="/signup" class="hover:text-teal-400 transition-colors">Register Laboratory Account</NuxtLink></li>
          <li><NuxtLink to="/account" class="hover:text-teal-400 transition-colors">My Lab Account</NuxtLink></li>
          <li><NuxtLink to="/account/licences" class="hover:text-teal-400 transition-colors">Manage Software Licences</NuxtLink></li>
          <li><NuxtLink to="/account/orders" class="hover:text-teal-400 transition-colors">Invoices & Receipts</NuxtLink></li>
          <li><NuxtLink to="/contact" class="hover:text-teal-400 transition-colors">Contact Support Team</NuxtLink></li>
          <li><NuxtLink to="/about" class="hover:text-teal-400 transition-colors">About Aarozi Healthcare</NuxtLink></li>
        </ul>
      </div>
    </div>

    <!-- Bottom Copyright & Compliance Strip -->
    <div class="border-t border-slate-900 bg-slate-950 py-6 text-[11px] text-slate-500">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex items-center space-x-2 text-center md:text-left">
          <span>&copy; {{ new Date().getFullYear() }} Aarozi Healthcare Systems. All rights reserved.</span>
          <span class="hidden md:inline">&bull;</span>
          <span class="hidden md:inline">Registered Healthcare Software in India</span>
        </div>

        <div class="flex flex-wrap items-center justify-center gap-4 text-slate-400">
          <NuxtLink to="/privacy" class="hover:text-teal-400 transition-colors">Privacy Policy</NuxtLink>
          <NuxtLink to="/terms" class="hover:text-teal-400 transition-colors">Terms of Service</NuxtLink>
          <NuxtLink to="/licence-terms" class="hover:text-teal-400 transition-colors">Software Licence Terms</NuxtLink>
          <NuxtLink to="/support" class="hover:text-teal-400 transition-colors">Security & Offline Assurance</NuxtLink>
        </div>
      </div>
    </div>
  </footer>
</template>


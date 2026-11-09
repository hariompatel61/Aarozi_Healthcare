<script setup lang="ts">
import { ref } from 'vue'

const activeTab = ref('licenses')
const isTransferModalOpen = ref(false)
const transferReason = ref('')
const newMachineId = ref('')

const customerData = ref({
  lab_name: 'Central Diagnostic Laboratory & Blood Center',
  contact_name: 'Dr. Ramesh K. Verma',
  email: 'ramesh.verma@centraldiagnostics.in',
  phone: '+91 98200 12345',
  gstin: '27AABCU9603R1ZM',
  plan_code: 'YEARLY_PRO',
  plan_name: 'Yearly Commercial Subscription',
  license_id: 'LIC-PROD-20261109-8F12',
  issued_at: '2026-11-09',
  valid_to: '2027-11-09',
  days_remaining: 365,
  status: 'ACTIVE',
  registered_machine_id: 'HW-89F4-A012-78BC',
  registered_ip: '192.168.1.100 (Master PC)',
  software_version: 'v1.0.4-LTS (Windows x64)',
  max_workstations: 15,
  active_workstations: 6,
  transfers_used: 0,
  max_transfers_per_year: 2,
})

const invoices = ref([
  {
    invoice_number: 'INV-AAR-202611-9014',
    date: '2026-11-09',
    description: 'Yearly Commercial LIS License (1 Year)',
    amount_inr: 17698.82,
    status: 'PAID',
    payment_method: 'UPI / Razorpay',
  },
])

function submitHardwareTransfer() {
  if (!newMachineId.value.trim() || !transferReason.value.trim()) {
    alert('Please enter the new Machine Hardware Fingerprint and Reason.')
    return
  }
  customerData.value.registered_machine_id = newMachineId.value.trim()
  customerData.value.transfers_used += 1
  isTransferModalOpen.value = false
  alert('Hardware migration recorded! Download your updated license file.')
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased text-xs">
    <!-- Portal Header -->
    <header class="bg-white border-b border-slate-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <NuxtLink to="/" class="flex items-center space-x-2">
            <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-black text-sm">
              A
            </div>
            <span class="font-bold text-slate-900 text-sm">Aarozi Healthcare</span>
          </NuxtLink>
          <span class="text-slate-300">/</span>
          <span class="font-semibold text-slate-700">Customer License &amp; Downloads Portal</span>
        </div>

        <div class="flex items-center space-x-3">
          <span class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
            &bull; Commercial Account Active
          </span>
          <NuxtLink to="/" class="text-slate-500 hover:text-slate-800 transition">Back to Main Website</NuxtLink>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <!-- Laboratory Summary Banner -->
      <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center space-x-2">
            <h1 class="text-lg font-bold text-slate-900">{{ customerData.lab_name }}</h1>
            <span class="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-bold border border-indigo-100 text-[10px]">
              {{ customerData.plan_name }}
            </span>
          </div>
          <p class="text-slate-500 mt-1">
            Registered To: {{ customerData.contact_name }} &bull; {{ customerData.email }} &bull; GSTIN: {{ customerData.gstin }}
          </p>
        </div>

        <div class="flex items-center space-x-2">
          <NuxtLink
            to="/dashboard"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-xs transition"
          >
            Launch LIS Workstation &rarr;
          </NuxtLink>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex space-x-2 border-b border-slate-200 pb-2">
        <button
          type="button"
          class="px-4 py-2 font-semibold rounded-lg transition"
          :class="activeTab === 'licenses' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
          @click="activeTab = 'licenses'"
        >
          Active License &amp; Keys
        </button>
        <button
          type="button"
          class="px-4 py-2 font-semibold rounded-lg transition"
          :class="activeTab === 'downloads' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
          @click="activeTab = 'downloads'"
        >
          Installer &amp; Updates (v1.0.4)
        </button>
        <button
          type="button"
          class="px-4 py-2 font-semibold rounded-lg transition"
          :class="activeTab === 'hardware' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
          @click="activeTab = 'hardware'"
        >
          Master PC Binding &amp; Transfers
        </button>
        <button
          type="button"
          class="px-4 py-2 font-semibold rounded-lg transition"
          :class="activeTab === 'invoices' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
          @click="activeTab = 'invoices'"
        >
          GST Invoices &amp; Payments
        </button>
      </div>

      <!-- Tab 1: Licenses -->
      <div v-if="activeTab === 'licenses'" class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="md:col-span-2 bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4">
          <div class="flex justify-between items-center border-b border-slate-100 pb-3">
            <h2 class="font-bold text-slate-900 text-sm">Cryptographically Sealed Ed25519 License</h2>
            <span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">
              Valid for {{ customerData.days_remaining }} Days
            </span>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <span class="text-slate-400 block">License Document ID</span>
              <span class="font-mono font-bold text-slate-800">{{ customerData.license_id }}</span>
            </div>
            <div>
              <span class="text-slate-400 block">Expiration Date</span>
              <span class="font-semibold text-slate-800">{{ customerData.valid_to }} (+30 Day Grace)</span>
            </div>
            <div>
              <span class="text-slate-400 block">Max Concurrent LAN Workstations</span>
              <span class="font-semibold text-slate-800">{{ customerData.max_workstations }} Workstations (6 Active)</span>
            </div>
            <div>
              <span class="text-slate-400 block">Signature Verification</span>
              <span class="font-semibold text-emerald-600">Ed25519 Verified Locally</span>
            </div>
          </div>

          <!-- Entitlements Grid -->
          <div class="pt-2">
            <span class="text-slate-400 block mb-2 font-medium">Included Clinical &amp; Operational Modules</span>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <span class="px-2.5 py-1 rounded bg-slate-50 border border-slate-200 text-slate-700">&check; Pathology Desk</span>
              <span class="px-2.5 py-1 rounded bg-slate-50 border border-slate-200 text-slate-700">&check; Clinical Biochemistry</span>
              <span class="px-2.5 py-1 rounded bg-slate-50 border border-slate-200 text-slate-700">&check; Hematology Workstation</span>
              <span class="px-2.5 py-1 rounded bg-slate-50 border border-slate-200 text-slate-700">&check; Blood Bank Management</span>
              <span class="px-2.5 py-1 rounded bg-slate-50 border border-slate-200 text-slate-700">&check; Cashier Billing &amp; Invoices</span>
              <span class="px-2.5 py-1 rounded bg-slate-50 border border-slate-200 text-slate-700">&check; Analyzer Interfacing</span>
            </div>
          </div>

          <div class="pt-4 flex items-center space-x-3">
            <a
              href="/licensing/status"
              target="_blank"
              class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg shadow-xs transition"
            >
              Download Signed .lic License File
            </a>
            <button
              type="button"
              class="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-semibold rounded-lg transition"
              @click="alert('License signature copied to clipboard!')"
            >
              Copy Signature Key
            </button>
          </div>
        </div>

        <!-- Quick Help Box -->
        <div class="bg-indigo-900 rounded-2xl p-6 text-white space-y-4 shadow-xs">
          <h3 class="font-bold text-sm">Offline License Instructions</h3>
          <ol class="list-decimal list-inside space-y-2 text-indigo-200 text-[11px] leading-relaxed">
            <li>Download the <code>.lic</code> file onto a USB thumb drive.</li>
            <li>Take it to your Laboratory Master PC.</li>
            <li>Open Aarozi Healthcare &rarr; <strong>Settings &rarr; System Licensing</strong>.</li>
            <li>Click <strong>Import License</strong> and select your file.</li>
            <li>The system unlocks all clinical modules immediately!</li>
          </ol>
        </div>
      </div>

      <!-- Tab 2: Downloads -->
      <div v-if="activeTab === 'downloads'" class="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4">
        <h2 class="font-bold text-slate-900 text-sm">Download Official Software Installers</h2>
        <p class="text-slate-500">
          Official Windows 10 &amp; 11 64-bit release. Includes embedded server runtime, SQLite database engine, and firewall rules.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div class="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-3">
            <div class="flex justify-between items-start">
              <div>
                <h3 class="font-bold text-slate-900">Aarozi-Healthcare-Setup-v1.0.0.exe</h3>
                <span class="text-slate-500 text-[11px]">Size: ~48 MB &bull; SHA-256 Verified</span>
              </div>
              <span class="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-bold text-[10px]">LTS RELEASE</span>
            </div>
            <a
              href="#"
              class="block text-center py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-xs transition"
              @click.prevent="alert('Downloading Aarozi-Healthcare-Setup-v1.0.0.exe from Cloudflare R2...')"
            >
              Download Windows 64-bit Installer (.exe)
            </a>
          </div>

          <div class="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-3">
            <div class="flex justify-between items-start">
              <div>
                <h3 class="font-bold text-slate-900">Aarozi Standalone ZIP Package</h3>
                <span class="text-slate-500 text-[11px]">Portable folder without setup wizard</span>
              </div>
              <span class="px-2 py-0.5 rounded bg-slate-200 text-slate-700 font-bold text-[10px]">PORTABLE</span>
            </div>
            <a
              href="#"
              class="block text-center py-2 bg-slate-800 hover:bg-slate-900 text-white font-semibold rounded-lg shadow-xs transition"
              @click.prevent="alert('Downloading Portable ZIP Package...')"
            >
              Download Portable ZIP Package
            </a>
          </div>
        </div>
      </div>

      <!-- Tab 3: Hardware Binding -->
      <div v-if="activeTab === 'hardware'" class="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4">
        <div class="flex justify-between items-center border-b border-slate-100 pb-3">
          <div>
            <h2 class="font-bold text-slate-900 text-sm">Laboratory Master Server Hardware Identity</h2>
            <p class="text-slate-500 mt-0.5">Your commercial license is bound to this PC. All other LAN workstations connect through it.</p>
          </div>
          <button
            type="button"
            class="px-3 py-1.5 bg-amber-50 text-amber-800 border border-amber-200 rounded-lg font-semibold hover:bg-amber-100 transition"
            @click="isTransferModalOpen = true"
          >
            Transfer to New PC
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <span class="text-slate-400 block">Registered Machine ID</span>
            <span class="font-mono font-bold text-slate-800 text-sm">{{ customerData.registered_machine_id }}</span>
          </div>
          <div class="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <span class="text-slate-400 block">Local LAN Address</span>
            <span class="font-semibold text-slate-800 text-sm">{{ customerData.registered_ip }}</span>
          </div>
          <div class="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <span class="text-slate-400 block">Hardware Migrations Used</span>
            <span class="font-semibold text-slate-800 text-sm">{{ customerData.transfers_used }} of {{ customerData.max_transfers_per_year }} allowed this year</span>
          </div>
        </div>
      </div>

      <!-- Tab 4: Invoices -->
      <div v-if="activeTab === 'invoices'" class="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-4">
        <h2 class="font-bold text-slate-900 text-sm">GST Invoices &amp; Payment History</h2>

        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b border-slate-200 text-slate-400 font-medium">
                <th class="py-2.5">Invoice #</th>
                <th class="py-2.5">Date</th>
                <th class="py-2.5">Description</th>
                <th class="py-2.5">Amount (with 18% GST)</th>
                <th class="py-2.5">Payment Method</th>
                <th class="py-2.5">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="inv in invoices" :key="inv.invoice_number" class="border-b border-slate-100">
                <td class="py-3 font-mono font-bold text-indigo-600">{{ inv.invoice_number }}</td>
                <td class="py-3 text-slate-600">{{ inv.date }}</td>
                <td class="py-3 font-medium text-slate-900">{{ inv.description }}</td>
                <td class="py-3 font-semibold text-slate-900">₹{{ inv.amount_inr.toLocaleString('en-IN') }}</td>
                <td class="py-3 text-slate-600">{{ inv.payment_method }}</td>
                <td class="py-3">
                  <button
                    type="button"
                    class="text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer"
                    @click="alert(`Downloading GST Tax Invoice ${inv.invoice_number}...`)"
                  >
                    Download PDF
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>

    <!-- Hardware Transfer Modal -->
    <div v-if="isTransferModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
        <div class="flex justify-between items-center border-b border-slate-100 pb-3">
          <h3 class="font-bold text-slate-900 text-sm">Transfer License to New PC</h3>
          <button type="button" class="text-slate-400 hover:text-slate-600 text-lg cursor-pointer" @click="isTransferModalOpen = false">&times;</button>
        </div>

        <p class="text-slate-600 text-[11px] leading-relaxed">
          Use this if your laboratory master PC had a motherboard/disk failure or you upgraded to a new server.
        </p>

        <div class="space-y-3">
          <div>
            <label class="block font-medium text-slate-700 mb-1">New Machine Fingerprint (e.g. HW-99A1-B2C3-D4E5) *</label>
            <input
              v-model="newMachineId"
              type="text"
              required
              placeholder="HW-XXXX-XXXX-XXXX"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg uppercase focus:ring-1 focus:ring-indigo-500 focus:outline-hidden font-mono"
            />
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Reason for Transfer *</label>
            <input
              v-model="transferReason"
              type="text"
              required
              placeholder="e.g. Motherboard upgraded, PC replaced"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:outline-hidden"
            />
          </div>
        </div>

        <div class="flex justify-end space-x-2 pt-2">
          <button
            type="button"
            class="px-4 py-2 border border-slate-300 rounded-lg font-semibold hover:bg-slate-50 transition"
            @click="isTransferModalOpen = false"
          >
            Cancel
          </button>
          <button
            type="button"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-xs transition"
            @click="submitHardwareTransfer"
          >
            Confirm &amp; Generate License
          </button>
        </div>
      </div>
    </div>
  </div>
</template>


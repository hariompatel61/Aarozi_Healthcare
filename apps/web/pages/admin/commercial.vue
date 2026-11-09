<script setup lang="ts">
import { ref } from 'vue'

const activeAdminTab = ref('labs')
const searchQuery = ref('')
const isManualIssueOpen = ref(false)

const manualForm = ref({
  lab_name: '',
  contact_name: '',
  email: '',
  phone: '',
  plan_code: 'COMMERCIAL_PRO',
  duration_days: 365,
  hardware_id: '',
})

const laboratories = ref([
  {
    id: 'lab-01',
    name: 'Central Pathology & Diagnostic Center',
    city: 'Mumbai, MH',
    phone: '+91 98200 12345',
    plan: 'COMMERCIAL_PRO',
    valid_until: '2027-11-09',
    status: 'ACTIVE',
    workstations: 15,
    machine_id: 'HW-89F4-A012-78BC',
    revenue_inr: 17698.82,
  },
  {
    id: 'lab-02',
    name: 'Apollo Clinical Diagnostic Lab',
    city: 'Bengaluru, KA',
    phone: '+91 99001 98765',
    plan: 'LIFETIME_ENTERPRISE',
    valid_until: 'Perpetual (Never)',
    status: 'ACTIVE',
    workstations: 50,
    machine_id: 'HW-12AB-34CD-56EF',
    revenue_inr: 47198.82,
  },
  {
    id: 'lab-03',
    name: 'City Care Pathology & Blood Bank',
    city: 'Pune, MH',
    phone: '+91 94220 54321',
    plan: 'COMMERCIAL_PRO',
    valid_until: '2026-12-01',
    status: 'EXPIRING_SOON',
    workstations: 10,
    machine_id: 'HW-77BC-88DE-99FA',
    revenue_inr: 17698.82,
  },
])

const recentTransactions = ref([
  { id: 'tx-101', lab: 'Central Pathology', amount: 17698.82, status: 'CAPTURED', method: 'UPI', date: 'Today, 11:36 AM' },
  { id: 'tx-102', lab: 'Apollo Clinical', amount: 47198.82, status: 'CAPTURED', method: 'NetBanking', date: 'Yesterday' },
])

function issueManualLicense() {
  if (!manualForm.value.lab_name || !manualForm.value.email) {
    alert('Please enter Lab Name and Email.')
    return
  }
  laboratories.value.unshift({
    id: `lab-${Date.now()}`,
    name: manualForm.value.lab_name,
    city: 'Manual Offline Issuance',
    phone: manualForm.value.phone || 'N/A',
    plan: manualForm.value.plan_code,
    valid_until: manualForm.value.plan_code === 'LIFETIME_ENTERPRISE' ? 'Perpetual' : '365 Days',
    status: 'ACTIVE',
    workstations: 15,
    machine_id: manualForm.value.hardware_id || 'ANY_MACHINE',
    revenue_inr: manualForm.value.plan_code === 'LIFETIME_ENTERPRISE' ? 47198.82 : 17698.82,
  })
  isManualIssueOpen.value = false
  alert(`Commercial License created and cryptographically signed for ${manualForm.value.lab_name}!`)
}

function showAlert(msg: string) {
  if (typeof window !== 'undefined') {
    window.alert(msg)
  }
}

function revokeLicense(labId: string) {
  if (confirm(`Are you sure you want to revoke license for ${labId}?`)) {
    const lab = laboratories.value.find(l => l.id === labId)
    if (lab) lab.status = 'REVOKED'
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased text-xs">
    <!-- Admin Top Nav -->
    <header class="bg-slate-900 text-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <NuxtLink to="/" class="flex items-center space-x-2">
            <div class="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center font-black text-sm">
              A
            </div>
            <span class="font-bold text-sm tracking-tight">Aarozi Healthcare &mdash; Vendor Master Console</span>
          </NuxtLink>
        </div>

        <div class="flex items-center space-x-4">
          <span class="text-slate-400">Vendor SuperAdmin</span>
          <NuxtLink to="/dashboard" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-semibold transition">
            Launch LIS App &rarr;
          </NuxtLink>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <!-- Top Metrics -->
      <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span class="text-slate-400 font-medium block">Total Active Labs</span>
          <span class="text-2xl font-black text-slate-900 mt-1 block">142</span>
          <span class="text-emerald-600 text-[11px] font-semibold mt-1 block">&uarr; +18 this month</span>
        </div>
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span class="text-slate-400 font-medium block">Annual Recurring Revenue (ARR)</span>
          <span class="text-2xl font-black text-indigo-600 mt-1 block">₹28.4 Lakhs</span>
          <span class="text-slate-400 text-[11px] mt-1 block">94% renewal rate</span>
        </div>
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span class="text-slate-400 font-medium block">Lifetime Licenses Issued</span>
          <span class="text-2xl font-black text-slate-900 mt-1 block">38</span>
          <span class="text-slate-400 text-[11px] mt-1 block">CAPEX purchases</span>
        </div>
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <span class="text-slate-400 font-medium block">Pending Hardware Migrations</span>
          <span class="text-2xl font-black text-amber-600 mt-1 block">1</span>
          <span class="text-slate-400 text-[11px] mt-1 block">Review requested</span>
        </div>
      </div>

      <!-- Action & Navigation Bar -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div class="flex space-x-2">
          <button
            type="button"
            class="px-4 py-2 font-semibold rounded-lg transition"
            :class="activeAdminTab === 'labs' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
            @click="activeAdminTab = 'labs'"
          >
            Registered Labs
          </button>
          <button
            type="button"
            class="px-4 py-2 font-semibold rounded-lg transition"
            :class="activeAdminTab === 'payments' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
            @click="activeAdminTab = 'payments'"
          >
            Razorpay Transactions
          </button>
        </div>

        <div class="flex items-center space-x-3">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search lab name or phone..."
            class="px-3 py-1.5 border border-slate-300 rounded-lg text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-hidden"
          />
          <button
            type="button"
            class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg shadow-xs transition"
            @click="isManualIssueOpen = true"
          >
            + Issue Offline License
          </button>
        </div>
      </div>

      <!-- Laboratories Table -->
      <div v-if="activeAdminTab === 'labs'" class="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold">
              <tr>
                <th class="p-4">Laboratory Name</th>
                <th class="p-4">Plan</th>
                <th class="p-4">Expires</th>
                <th class="p-4">Machine ID</th>
                <th class="p-4">Status</th>
                <th class="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="lab in laboratories" :key="lab.id" class="hover:bg-slate-50/60">
                <td class="p-4">
                  <div class="font-bold text-slate-900">{{ lab.name }}</div>
                  <div class="text-slate-400 text-[11px]">{{ lab.city }} &bull; {{ lab.phone }}</div>
                </td>
                <td class="p-4">
                  <span class="px-2 py-0.5 rounded font-bold text-[10px]" :class="lab.plan === 'LIFETIME_ENTERPRISE' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-100 text-slate-700'">
                    {{ lab.plan }}
                  </span>
                </td>
                <td class="p-4 font-semibold text-slate-700">{{ lab.valid_until }}</td>
                <td class="p-4 font-mono text-[11px] text-slate-600">{{ lab.machine_id }}</td>
                <td class="p-4">
                  <span
                    class="px-2 py-0.5 rounded-full font-bold text-[10px]"
                    :class="{
                      'bg-emerald-50 text-emerald-700': lab.status === 'ACTIVE',
                      'bg-amber-50 text-amber-700': lab.status === 'EXPIRING_SOON',
                      'bg-rose-50 text-rose-700': lab.status === 'REVOKED',
                    }"
                  >
                    {{ lab.status }}
                  </span>
                </td>
                <td class="p-4 text-right space-x-2">
                  <button
                    type="button"
                    class="text-indigo-600 hover:text-indigo-800 font-semibold"
                    @click="showAlert(`Exporting signed license for ${lab.name}...`)"
                  >
                    Download .lic
                  </button>
                  <button
                    v-if="lab.status !== 'REVOKED'"
                    type="button"
                    class="text-rose-600 hover:text-rose-800 font-semibold"
                    @click="revokeLicense(lab.id)"
                  >
                    Revoke
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Transactions Tab -->
      <div v-if="activeAdminTab === 'payments'" class="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold">
              <tr>
                <th class="p-4">Transaction ID</th>
                <th class="p-4">Customer Lab</th>
                <th class="p-4">Amount</th>
                <th class="p-4">Status</th>
                <th class="p-4">Method</th>
                <th class="p-4">Date</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="tx in recentTransactions" :key="tx.id">
                <td class="p-4 font-mono font-bold text-slate-800">{{ tx.id }}</td>
                <td class="p-4 font-medium text-slate-900">{{ tx.lab }}</td>
                <td class="p-4 font-bold text-slate-900">₹{{ tx.amount.toLocaleString('en-IN') }}</td>
                <td class="p-4">
                  <span class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold text-[10px]">
                    {{ tx.status }}
                  </span>
                </td>
                <td class="p-4 text-slate-600">{{ tx.method }}</td>
                <td class="p-4 text-slate-500">{{ tx.date }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>

    <!-- Manual License Issuance Modal -->
    <div v-if="isManualIssueOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
        <div class="flex justify-between items-center border-b border-slate-100 pb-3">
          <h3 class="font-bold text-slate-900 text-sm">Issue Offline Commercial License</h3>
          <button type="button" class="text-slate-400 hover:text-slate-600 text-lg cursor-pointer" @click="isManualIssueOpen = false">&times;</button>
        </div>

        <div class="space-y-3">
          <div>
            <label class="block font-medium text-slate-700 mb-1">Laboratory Name *</label>
            <input v-model="manualForm.lab_name" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-lg" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Plan</label>
              <select v-model="manualForm.plan_code" class="w-full px-3 py-2 border border-slate-300 rounded-lg">
                <option value="COMMERCIAL_PRO">Yearly Pro (₹14,999)</option>
                <option value="LIFETIME_ENTERPRISE">Lifetime (₹39,999)</option>
              </select>
            </div>
            <div>
              <label class="block font-medium text-slate-700 mb-1">Duration Days</label>
              <input v-model.number="manualForm.duration_days" type="number" class="w-full px-3 py-2 border border-slate-300 rounded-lg" />
            </div>
          </div>
          <div>
            <label class="block font-medium text-slate-700 mb-1">Customer Email *</label>
            <input v-model="manualForm.email" type="email" class="w-full px-3 py-2 border border-slate-300 rounded-lg" />
          </div>
          <div>
            <label class="block font-medium text-slate-700 mb-1">Hardware Fingerprint (Optional Binding)</label>
            <input v-model="manualForm.hardware_id" type="text" placeholder="HW-XXXX-XXXX-XXXX" class="w-full px-3 py-2 border border-slate-300 rounded-lg font-mono uppercase" />
          </div>
        </div>

        <div class="flex justify-end space-x-2 pt-2">
          <button type="button" class="px-4 py-2 border border-slate-300 rounded-lg font-semibold" @click="isManualIssueOpen = false">Cancel</button>
          <button type="button" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-xs" @click="issueManualLicense">
            Sign &amp; Generate License (.lic)
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

